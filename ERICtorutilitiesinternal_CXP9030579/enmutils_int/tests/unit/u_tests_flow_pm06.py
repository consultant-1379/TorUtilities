#!/usr/bin/env python
import unittest2
from enmutils.lib.exceptions import EnvironWarning
from enmutils_int.lib.nrm_default_configurations.five_network import five_k_network
from enmutils_int.lib.nrm_default_configurations.forty_network import forty_k_network
from enmutils_int.lib.nrm_default_configurations.one_hundred_network import one_hundred_k_network
from enmutils_int.lib.nrm_default_configurations.sixty_network import sixty_k_network
from enmutils_int.lib.nrm_default_configurations.soem_five_network import soem_five_k_network
from enmutils_int.lib.pm_subscriptions import StatisticalSubscription
from enmutils_int.lib.workload import pm_06
from mock import patch, Mock, PropertyMock, call
from testslib import unit_test_utils


class Pm06ProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.user = Mock(username="some_user")
        self.users = [Mock() for _ in xrange(15)]
        self.nodes = self.setup_nodes()
        self.profile = pm_06.PM_06()
        self.profile.MAX_NODES_TO_ADD = 7
        self.NUM_USERS = 0
        self.profile.subscriptions = []
        self.profile.teardown_list = []

        soem_pm06_settings = forty_k_network["forty_k_network"]["pm"]["PM_06"]
        for key, value in soem_pm06_settings.items():
            setattr(self.profile, key, value)

    def tearDown(self):
        unit_test_utils.tear_down()

    @staticmethod
    def setup_nodes():
        return [Mock()] * 10

    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.delete_stats_subscriptions")
    @patch("enmutils_int.lib.workload.pm_06.create_and_delete_cell_and_stats_alternatively")
    @patch("enmutils_int.lib.workload.pm_06.create_and_activate_stats_subscriptions")
    def test_create_delete_subscriptions_task_set__is_successful(self, *_):
        self.profile.CELLTRACE_SUPPORTED_NODE_TYPES = ["ERBS", "MSRBS_V2", "RadioNode"]
        self.profile.STATS_UNSUPPORTED_NODE_TYPES = ["TCU02", "SIU02", "EPG", "vEPG", "WMG", "vWMG"]

        pm_06.create_delete_subscriptions_task_set(self.users, self.nodes, self.profile)

    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.time.sleep")
    @patch("enmutils.lib.enm_user_2.User.delete_request")
    @patch("enmutils_int.lib.workload.pm_06.StatisticalSubscription")
    @patch("enmutils_int.lib.workload.pm_06.CelltraceSubscription")
    def test_create_delete_subscriptions_task_set__raises_environwarning_if_not_enough_nodes(self, *_):
        self.profile.CELLTRACE_SUPPORTED_NODE_TYPES = ["ERBS", "MSRBS_V2", "RadioNode"]

        self.assertRaises(EnvironWarning,
                          pm_06.create_delete_subscriptions_task_set, self.users, [], self.profile)

    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.time.sleep")
    @patch("enmutils_int.lib.workload.pm_06.get_pm_home")
    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception")
    @patch("enmutils_int.lib.workload.pm_06.StatisticalSubscription")
    def test_create_and_activate_stats_subscriptions__is_successful(self, *_):
        self.profile.subscriptions = []
        pm_06.create_and_activate_stats_subscriptions(self.users, self.profile, self.nodes)
        self.assertEqual(5, len(self.profile.subscriptions))

    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.time.sleep")
    @patch("enmutils_int.lib.workload.pm_06.get_pm_home")
    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception")
    @patch("enmutils_int.lib.workload.pm_06.StatisticalSubscription")
    def test_create_and_activate_stats_subscriptions__adds_errors_if_subs_cant_be_created(
            self, mock_stats_sub, mock_add_error_as_exception, *_):
        mock_stats_sub.return_value.create.side_effect = Exception
        self.profile.subscriptions = []

        pm_06.create_and_activate_stats_subscriptions(self.users, self.profile, self.nodes)
        self.assertEqual(0, len(self.profile.subscriptions))
        self.assertEqual(5, mock_add_error_as_exception.call_count)

    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.time.sleep")
    @patch("enmutils_int.lib.workload.pm_06.get_pm_home")
    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception")
    @patch("enmutils_int.lib.workload.pm_06.StatisticalSubscription")
    def test_create_and_activate_stats_subscriptions__adds_errors_if_subs_cant_be_activated(
            self, mock_stats_sub, mock_add_error_as_exception, *_):
        mock_stats_sub.return_value.activate.side_effect = Exception

        pm_06.create_and_activate_stats_subscriptions(self.users, self.profile, self.nodes)
        self.assertEqual(5, len(self.profile.subscriptions))
        self.assertEqual(1, mock_add_error_as_exception.call_count)

    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.get_pm_home")
    @patch("enmutils_int.lib.profile.TeardownList")
    @patch("enmutils_int.lib.workload.pm_06.time.sleep")
    @patch("enmutils_int.lib.workload.pm_06.get_int_time_in_secs_since_epoch")
    @patch("enmutils_int.lib.workload.pm_06.StatisticalSubscription")
    @patch("enmutils_int.lib.workload.pm_06.CelltraceSubscription")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception")
    def test_create_and_delete_cell_and_stats_alternatively__is_successful(
            self, mock_add_error_as_exception, mock_cell_sub, mock_stats_sub, mock_get_int_time_in_secs_since_epoch,
            mock_sleep, *_):
        interval = 60 * 60
        time_taken = 10
        times = [interval, interval + time_taken]
        for i in xrange(20):
            time_before = (i + 2) * interval
            time_after = time_before + time_taken
            times += [time_before, time_after]
        mock_get_int_time_in_secs_since_epoch.side_effect = times

        pm_06.create_and_delete_cell_and_stats_alternatively(self.users, self.profile, self.nodes, self.nodes)
        self.assertEqual(0, len(self.profile.teardown_list))
        self.assertEqual(mock_stats_sub.return_value.create.call_count, 5)
        self.assertEqual(mock_cell_sub.return_value.create.call_count, 5)
        self.assertEqual(mock_stats_sub.return_value.delete.call_count, 5)
        self.assertEqual(mock_cell_sub.return_value.delete.call_count, 5)
        self.assertFalse(mock_add_error_as_exception.called)
        mock_sleep_calls = [call(interval)] + [call(interval - time_taken)] * 19
        self.assertEqual(mock_sleep_calls, mock_sleep.mock_calls)

    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.get_int_time_in_secs_since_epoch")
    @patch("enmutils_int.lib.workload.pm_06.time.sleep")
    @patch("enmutils_int.lib.workload.pm_06.get_pm_home")
    @patch("enmutils_int.lib.profile.TeardownList")
    @patch("enmutils_int.lib.workload.pm_06.StatisticalSubscription")
    @patch("enmutils_int.lib.workload.pm_06.CelltraceSubscription")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception")
    def test_create_and_delete_cell_and_stats_alternatively__is_successful_without_cell_nodes(
            self, mock_add_error_as_exception, mock_celltrace_sub, mock_stats_sub, *_):
        pm_06.create_and_delete_cell_and_stats_alternatively(self.users, self.profile, self.nodes, [])
        self.assertEqual(0, len(self.profile.teardown_list))
        self.assertEqual(mock_stats_sub.return_value.create.call_count, 5)
        self.assertEqual(mock_stats_sub.return_value.delete.call_count, 5)
        self.assertFalse(mock_celltrace_sub.called)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.get_int_time_in_secs_since_epoch")
    @patch("enmutils_int.lib.workload.pm_06.time.sleep")
    @patch("enmutils_int.lib.workload.pm_06.get_pm_home")
    @patch("enmutils_int.lib.profile.TeardownList")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception")
    @patch("enmutils_int.lib.workload.pm_06.StatisticalSubscription")
    @patch("enmutils_int.lib.workload.pm_06.CelltraceSubscription")
    def test_create_and_delete_cell_and_stats_alternatively__adds_errors_if_subs_cant_be_created(
            self, mock_cell_sub, mock_stat_sub, mock_add_error_as_exception, *_):
        mock_cell_sub.return_value.create.side_effect = Exception
        mock_stat_sub.return_value.delete.side_effect = Exception

        pm_06.create_and_delete_cell_and_stats_alternatively(self.users, self.profile, self.nodes, self.nodes)
        self.assertEqual(0, len(self.profile.teardown_list))
        self.assertEqual(10, mock_add_error_as_exception.call_count)

    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.time.sleep")
    @patch("enmutils_int.lib.workload.pm_06.get_pm_home")
    @patch("enmutils_int.lib.pm_subscriptions.Subscription.state", new_callable=PropertyMock, return_value="INACTIVE")
    @patch("enmutils_int.lib.profile.TeardownList")
    @patch("enmutils_int.lib.workload.pm_06.StatisticalSubscription.deactivate")
    @patch("enmutils_int.lib.workload.pm_06.StatisticalSubscription.delete")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception")
    def test_delete_stats_subscriptions__is_successful_and_teardown_list_is_empty(
            self, mock_add_error_as_exception, mock_delete, mock_deactivate, *_):
        subscriptions = []
        teardown_list = []
        for _ in xrange(5):
            name = "sub{0}".format(_)

            subscription = StatisticalSubscription(name=name)
            subscriptions.append(subscription)
            teardown_list.append(subscription)

        self.profile.subscriptions = subscriptions
        self.profile.teardown_list = teardown_list

        pm_06.delete_stats_subscriptions(self.users, self.profile)

        self.assertFalse(mock_deactivate.called)
        self.assertTrue(mock_delete.called)
        self.assertEqual(0, len(self.profile.teardown_list))
        self.assertFalse(mock_add_error_as_exception.called)
        self.assertEqual(0, len(self.profile.subscriptions))

    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.time.sleep")
    @patch("enmutils_int.lib.workload.pm_06.get_pm_home")
    @patch("enmutils_int.lib.profile.TeardownList")
    @patch("enmutils_int.lib.pm_subscriptions.Subscription.state", new_callable=PropertyMock, return_value="ACTIVE")
    @patch("enmutils_int.lib.workload.pm_06.StatisticalSubscription.deactivate")
    @patch("enmutils_int.lib.workload.pm_06.StatisticalSubscription.delete")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception")
    def test_delete_stats_subscriptions__delete_throws_exception(
            self, mock_add_error_as_exception, mock_delete, mock_deactivate, *_):
        subscriptions = []
        teardown_list = []

        for _ in xrange(5):
            name = "sub{0}".format(_)
            subscription = StatisticalSubscription(name=name)

            mock_delete.side_effect = Exception
            subscriptions.append(subscription)
            teardown_list.append(subscription)

        self.profile.subscriptions = subscriptions
        self.profile.teardown_list = teardown_list

        pm_06.delete_stats_subscriptions(self.users, self.profile)
        self.assertTrue(mock_deactivate.called)
        self.assertTrue(mock_delete.called)
        self.assertEqual(0, len(self.profile.teardown_list))
        self.assertEqual(mock_add_error_as_exception.call_count, 5)

    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.time.sleep")
    @patch("enmutils_int.lib.workload.pm_06.randint", return_value=2)
    @patch("enmutils_int.lib.workload.pm_06.get_nodes_to_be_updated_for_subscription")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception")
    def test_add_delete_nodes_task_set_is__successful(
            self, mock_add_error_as_exception, mock_get_nodes_to_be_updated_for_subscription, *_):
        self.profile.MAX_NODES_TO_ADD = 5
        sub = Mock()
        sub.name = 'PM-WORKER-4'
        self.profile.subscriptions = [sub]
        pm_06.add_delete_nodes_task_set(self.users, self.nodes, self.profile)

        add_call_count = delete_call_count = 0
        for item in mock_get_nodes_to_be_updated_for_subscription.mock_calls:
            if item == call("Add", sub, self.nodes):
                add_call_count += 1
            if item == call("Delete", sub, self.nodes):
                delete_call_count += 1

        self.assertEqual(self.profile.MAX_NODES_TO_ADD, add_call_count)
        self.assertEqual(self.profile.MAX_NODES_TO_ADD, delete_call_count)
        self.assertFalse(mock_add_error_as_exception.called)
        self.assertEqual(mock_get_nodes_to_be_updated_for_subscription.mock_calls[0],
                         call("Add", sub, self.nodes))

    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.time.sleep")
    @patch("enmutils_int.lib.workload.pm_06.randint", return_value=3)
    @patch("enmutils_int.lib.workload.pm_06.get_nodes_to_be_updated_for_subscription")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception")
    def test_add_delete_nodes_task_set__adds_error_if_update_fails(self, mock_add_error_as_exception, *_):
        self.profile.MAX_NODES_TO_ADD = 5
        sub = Mock()
        sub1 = Mock()
        sub.name = 'PM-WORKER-4'
        sub.update.side_effect = Exception("update failed")
        sub1.name = 'PM_WORKER-5'
        self.profile.subscriptions = [sub, sub1]
        pm_06.add_delete_nodes_task_set(self.users, self.nodes, self.profile)
        self.assertEqual(self.profile.MAX_NODES_TO_ADD * 2, mock_add_error_as_exception.call_count)

    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.time.sleep")
    @patch("enmutils_int.lib.workload.pm_06.randint", return_value=3)
    @patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception")
    def test_activate_deactivate_subscriptions__is_successful(self, mock_add_error_as_exception, *_):
        sub = Mock()
        sub.name = 'PM-WORKER-3'
        self.profile.subscriptions = [sub]

        pm_06.activate_deactivate_subscriptions(self.users, self.nodes, self.profile)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.time.sleep")
    @patch("enmutils_int.lib.workload.pm_06.randint", side_effect=[3, 2, 2, 2, 2])
    @patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception")
    def test_activate_deactivate_subscriptions__fails(self, mock_add_error_as_exception, *_):
        sub = Mock()
        sub1 = Mock()
        sub.name = 'PM-WORKER-3'
        sub1.name = 'PM-WORKER-1'
        sub.activate.side_effect = Exception()
        sub.deactivate.side_effect = Exception()
        self.profile.subscriptions = [sub, sub1]

        pm_06.activate_deactivate_subscriptions(self.users, self.nodes, self.profile)
        self.assertEqual(2, mock_add_error_as_exception.call_count)

    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.time.sleep")
    @patch("enmutils_int.lib.workload.pm_06.randint")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception")
    def test_change_counters_task_set__is_successful(self, mock_add_error_as_exception, mock_randint, *_):
        mock_randint.side_effect = [i for i in range(40)]

        sub = Mock()
        sub1 = Mock()
        sub.name = 'PM-WORKER-3'
        sub1.name = 'PM-WORKER-1'
        self.profile.subscriptions = [sub, sub1]

        pm_06.change_counters_task_set(self.users, self.nodes, self.profile)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.time.sleep")
    @patch("enmutils_int.lib.workload.pm_06.randint", return_value=1)
    @patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception")
    def test_change_counters_task_set__fails(self, mock_add_error_as_exception, *_):
        sub = Mock()
        sub1 = Mock()
        sub.name = 'PM-WORKER-3'
        sub1.name = 'PM-WORKER-1'
        sub1.update.side_effect = Exception()
        self.profile.subscriptions = [sub, sub1]

        pm_06.change_counters_task_set(self.users, self.nodes, self.profile)
        self.assertEqual(20, mock_add_error_as_exception.call_count)

    @patch("enmutils_int.lib.workload.pm_06.time.sleep")
    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.performing_continuous_polling")
    def test_burst_polling_task_set__is_successful(self, mock_performing_continuous_polling, mock_stack, *_):
        mock_stack.return_value = [[0, 1, 2, "some_task_name"]]
        expected_polling_time = 60 * 60
        pm_06.burst_polling_task_set([self.user], [], self.profile)
        mock_performing_continuous_polling.assert_called_with(
            "Task 2 some_task_name:", self.user, expected_polling_time, self.profile)

    @patch("enmutils_int.lib.workload.pm_06.time.sleep")
    @patch("enmutils_int.lib.workload.pm_06.randint")
    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.performing_continuous_polling")
    def test_polling_task_set__is_successful(self, mock_performing_continuous_polling, mock_stack, mock_randint, *_):
        mock_stack.return_value = [[0, 1, 2, "some_task_name"]]
        mock_randint.return_value = 5
        expected_polling_time = 24 * 60 * 60 - 5 - 60
        pm_06.polling_task_set([self.user], [], self.profile)
        mock_performing_continuous_polling.assert_called_with(
            "Task 1 some_task_name:", self.user, expected_polling_time, self.profile)

    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.poll_pm", return_value=0)
    @patch("enmutils_int.lib.workload.pm_06.time.sleep")
    @patch("enmutils_int.lib.workload.pm_06.time.time")
    def test_performing_continuous_polling__is_successful(self, mock_time, mock_sleep, mock_poll_pm, *_):
        expected_polling_time = 24 * 60 * 60
        mock_time.side_effect = [1, 10, 10, expected_polling_time + 1]
        pm_06.performing_continuous_polling("some_task_name", self.user, expected_polling_time, self.profile)
        self.assertEqual(2, mock_poll_pm.call_count)
        self.assertEqual(1, mock_sleep.call_count)

    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception")
    @patch("enmutils_int.lib.workload.pm_06.poll_pm", side_effect=[0, 3])
    @patch("enmutils_int.lib.workload.pm_06.time.sleep")
    @patch("enmutils_int.lib.workload.pm_06.time.time")
    def test_performing_continuous_polling__is_successful_if_polling_returns_error(
            self, mock_time, mock_sleep, mock_poll_pm, mock_add_error_as_exception, *_):
        expected_polling_time = 24 * 60 * 60
        mock_time.side_effect = [1, 61, 61, expected_polling_time + 1]
        pm_06.performing_continuous_polling("some_task_name", self.user, expected_polling_time, self.profile)
        self.assertEqual(2, mock_poll_pm.call_count)
        self.assertFalse(mock_sleep.called)
        self.assertEqual(1, mock_add_error_as_exception.call_count)

    @patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception")
    def test_get_pm_home__is_successful(self, mock_add_error_as_exception):
        pm_06.get_pm_home(self.user, self.profile)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception")
    def test_get_pm_home__adds_error_to_profile_if_cannot_access_enm(self, mock_add_error_as_exception):
        self.user.get.side_effect = Exception
        pm_06.get_pm_home(self.user, self.profile)
        self.assertTrue(mock_add_error_as_exception.called)

    def test_poll_pm__is_successful(self):
        self.assertEqual(0, pm_06.poll_pm(self.user, self.profile))

    def test_poll_pm__returns_non_zero_result_if_cannot_access_enm(self):
        self.user.get.side_effect = Exception
        self.assertEqual(3, pm_06.poll_pm(self.user, self.profile))

    def test_poll_pm__returns_non_zero_result_if_get_returns_nok_response(self):
        self.user.get.return_value.ok = 0
        self.assertEqual(3, pm_06.poll_pm(self.user, self.profile))

    def test_task_executor__is_successful(self):
        mock_func = Mock()
        user_task_set = (self.user, mock_func)
        pm_06.task_executor(user_task_set, self.nodes, self.profile)
        self.assertTrue(mock_func.called)

    @patch("enmutils_int.lib.workload.pm_06.PM_06.deallocate_stats_unsupported_nodes")
    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.datetime.datetime")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.workload.pm_06.PM_06.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.sleep")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.create_tasksets")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.create_and_execute_threads")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.process_thread_queue_errors")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.create_profile_users")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception")
    @patch("enmutils_int.lib.workload.pm_06.Subscription")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.keep_running")
    def test_pm_06_run__is_successful(self, mock_keep_running, mock_subscription, mock_add_error_as_exception, *_):
        mock_keep_running.side_effect = [True, False]

        self.profile.run()
        self.assertFalse(mock_add_error_as_exception.called)
        self.assertTrue(mock_subscription.clean_subscriptions.called)

    @patch("enmutils_int.lib.workload.pm_06.PM_06.deallocate_stats_unsupported_nodes")
    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.datetime.datetime")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.workload.pm_06.PM_06.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.create_tasksets")
    @patch("enmutils_int.lib.profile.Profile.sleep")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.create_and_execute_threads")
    @patch("enmutils_int.lib.profile.Profile.process_thread_queue_errors")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception")
    @patch("enmutils_int.lib.workload.pm_06.Subscription")
    @patch("enmutils_int.lib.profile.Profile.keep_running")
    def test_pm_06_run__is_successful_for_each_network_type(
            self, mock_keep_running, *_):
        mock_keep_running.side_effect = [True, False]

        networks = [soem_five_k_network, five_k_network, forty_k_network, sixty_k_network, one_hundred_k_network]
        profile_name = self.profile.__class__.__name__

        for network in networks:
            network_name = network.keys()[0]
            pm_settings = network[network_name]["pm"]
            if profile_name in pm_settings.keys():
                for key, value in pm_settings[profile_name].items():
                    setattr(self.profile, key, value)

        self.profile.run()

    @patch("enmutils_int.lib.workload.pm_06.PM_06.deallocate_stats_unsupported_nodes")
    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.datetime.datetime")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.workload.pm_06.PM_06.sleep")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.process_thread_queue_errors")
    def test_pm_06_run__expected_arguments_are_submitted_to_threadqueue_for_the_soem_network(self, *_):
        soem_pm06_settings = soem_five_k_network["soem_five_k_network"]["pm"]["PM_06"]
        for key, value in soem_pm06_settings.items():
            setattr(self.profile, key, value)

        with patch("enmutils_int.lib.workload.pm_06.PM_06.get_nodes_list_by_attribute") as mock_nodes_list, \
                patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow."
                      "create_profile_users") as mock_create_users, \
                patch("enmutils_int.lib.workload.pm_06.PM_06."
                      "create_and_execute_threads") as mock_create_and_execute_threads, \
                patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception") as mock_add_error_as_exception, \
                patch("enmutils_int.lib.workload.pm_06.Subscription") as mock_subscription, \
                patch("enmutils_int.lib.profile.Profile.keep_running") as mock_keep_running:
            mock_keep_running.side_effect = [True, False]
            mock_nodes_list.return_value = self.nodes

            mock_users = [Mock()]
            mock_create_users.return_value = mock_users

            baseline_polling_taskset = [(mock_users, pm_06.polling_task_set)]
            burst_polling_taskset = [(mock_users, pm_06.burst_polling_task_set)]
            create_delete_subscriptions_taskset = [(mock_users, pm_06.create_delete_subscriptions_task_set)]
            change_counters_taskset = [(mock_users, pm_06.change_counters_task_set)]
            activate_deactivate_subs_taskset = [(mock_users, pm_06.activate_deactivate_subscriptions)]
            add_delete_nodes_taskset = [(mock_users, pm_06.add_delete_nodes_task_set)]

            task_sets = (baseline_polling_taskset + burst_polling_taskset + create_delete_subscriptions_taskset +
                         change_counters_taskset + activate_deactivate_subs_taskset + add_delete_nodes_taskset)

            self.profile.run()

            self.assertFalse(mock_add_error_as_exception.called)
            self.assertTrue(mock_subscription.clean_subscriptions.called)

            mock_create_and_execute_threads.assert_called_with(task_sets, self.profile.NUM_USERS,
                                                               func_ref=pm_06.task_executor,
                                                               args=[self.nodes, self.profile],
                                                               wait=self.profile.THREAD_QUEUE_TIMEOUT,
                                                               last_error_only=True)
            mock_create_users.assert_called_with(len(mock_users), self.profile.USER_ROLES, safe_request=True)

    def test_create_tasksets__is_successful(self):
        user = Mock()
        percentages = [6, 5, 4, 3, 2, 1]
        self.profile.PERCENT_USERS = {'baseline_polling': percentages[0],
                                      'burst_polling': percentages[1],
                                      'create_delete_sub': percentages[2],
                                      'change_counters': percentages[3],
                                      'activate_deactivate': percentages[4],
                                      'add_delete_nodes': percentages[5]}

        with patch("enmutils_int.lib.workload.pm_06.PM_06.create_users_based_on_percentage") \
                as mock_create_users_based_on_percentage, \
                patch("enmutils_int.lib.workload.pm_06.polling_task_set") as mock_polling_task_set, \
                patch("enmutils_int.lib.workload.pm_06.burst_polling_task_set") as mock_burst_polling_task_set, \
                patch("enmutils_int.lib.workload.pm_06.create_delete_subscriptions_task_set") \
                as mock_create_delete_subscriptions_task_set, \
                patch("enmutils_int.lib.workload.pm_06.change_counters_task_set") as mock_change_counters_task_set, \
                patch("enmutils_int.lib.workload.pm_06.activate_deactivate_subscriptions") \
                as mock_activate_deactivate_subscriptions, \
                patch("enmutils_int.lib.workload.pm_06.add_delete_nodes_task_set") as mock_add_delete_nodes_task_set:
            users_returned = []
            for i in xrange(len(percentages)):
                users_returned.append([user] * percentages[i])

            mock_create_users_based_on_percentage.side_effect = users_returned

            baseline_polling_taskset = [([user], mock_polling_task_set)] * percentages[0]
            burst_polling_taskset = [([user], mock_burst_polling_task_set)] * percentages[1]
            create_delete_subscriptions_taskset = [([user] * percentages[2], mock_create_delete_subscriptions_task_set)]
            change_counters_taskset = [([user] * percentages[3], mock_change_counters_task_set)]
            activate_deactivate_subs_taskset = [([user] * percentages[4], mock_activate_deactivate_subscriptions)]
            add_delete_nodes_taskset = [([user] * percentages[5], mock_add_delete_nodes_task_set)]

            task_sets = (baseline_polling_taskset + burst_polling_taskset + create_delete_subscriptions_taskset +
                         change_counters_taskset + activate_deactivate_subs_taskset + add_delete_nodes_taskset)

            self.assertEqual(task_sets, self.profile.create_tasksets())

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users")
    def test_create_users_based_on_percentage__is_successful(self, mock_create_users):
        self.NUM_USERS = 60
        users_created = [Mock()] * 15
        mock_create_users.return_value = users_created
        self.assertEqual(self.profile.create_users_based_on_percentage(25), users_created)

    @patch("enmutils_int.lib.workload.pm_06.PM_06.deallocate_stats_unsupported_nodes")
    @patch("enmutils_int.lib.workload.pm_06.inspect.stack")
    @patch("enmutils_int.lib.workload.pm_06.datetime.datetime")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.workload.pm_06.PM_06.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile.Profile.sleep")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.create_tasksets")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.create_and_execute_threads")
    @patch("enmutils_int.lib.profile.Profile.process_thread_queue_errors")
    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users")
    @patch("enmutils_int.lib.workload.pm_06.PM_06.add_error_as_exception")
    @patch("enmutils_int.lib.workload.pm_06.Subscription")
    @patch("enmutils_int.lib.profile.Profile.keep_running")
    def test_pm_06_run__adds_error_if_clean_subscriptions_throws_exception(
            self, mock_keep_running, mock_subscription, mock_add_error_as_exception, *_):
        mock_keep_running.side_effect = [True, False]
        mock_subscription.clean_subscriptions.side_effect = Exception()

        self.profile.run()
        self.assertTrue(mock_add_error_as_exception.called)

    def test_get_nodes_to_be_updated_for_subscription__is_successful_for_add_nodes(self):
        node_1 = Mock(node_id=1)
        node_2 = Mock(node_id=2)
        node_3 = Mock(node_id=3)
        profile_nodes = [node_1, node_2, node_3]
        subscription = Mock(nodes=profile_nodes[0:2])

        updated_nodes = pm_06.get_nodes_to_be_updated_for_subscription("Add", subscription, profile_nodes)
        self.assertEqual(updated_nodes, profile_nodes)

    def test_get_nodes_to_be_updated_for_subscription__is_successful_for_add_nodes_if_no_extra_nodes_avail(self):
        node_1 = Mock(node_id=1)
        node_2 = Mock(node_id=2)
        node_3 = Mock(node_id=3)
        profile_nodes = [node_1, node_2, node_3]
        subscription = Mock(nodes=profile_nodes)

        updated_nodes = pm_06.get_nodes_to_be_updated_for_subscription("Add", subscription, profile_nodes)
        self.assertEqual(updated_nodes, profile_nodes)

    def test_get_nodes_to_be_updated_for_subscription__is_successful_for_delete_nodes(self):
        node_1 = Mock(node_id=1)
        node_2 = Mock(node_id=2)
        node_3 = Mock(node_id=3)
        profile_nodes = [node_1, node_2, node_3]
        subscription = Mock(nodes=profile_nodes[0:2])

        updated_nodes = pm_06.get_nodes_to_be_updated_for_subscription("Delete", subscription, profile_nodes)
        self.assertEqual(len(updated_nodes), 1)

    def test_get_nodes_to_be_updated_for_subscription__is_successful_for_delete_nodes_if_only_one_node_in_sub(self):
        node_1 = Mock(node_id=1)
        node_2 = Mock(node_id=2)
        node_3 = Mock(node_id=3)
        profile_nodes = [node_1, node_2, node_3]
        subscription = Mock(nodes=profile_nodes[0:1])

        updated_nodes = pm_06.get_nodes_to_be_updated_for_subscription("Delete", subscription, profile_nodes)
        self.assertEqual(len(updated_nodes), 1)

    @patch("enmutils_int.lib.profile_flows.common_flows.common_flow.GenericFlow.create_profile_users")
    def test_create_users_based_on_percentage__returns_empty_list_if_user_percentage_is_zero(self, _):
        self.assertEqual([], self.profile.create_users_based_on_percentage(0))

    @patch("enmutils_int.lib.workload.pm_06.PM_06.update_profile_persistence_nodes_list")
    def test_deallocate_stats_unsupported_nodes__if_exclusive_nodes_are_exist(
            self, mock_update_profile_persistence_nodes_list):
        nodes = [Mock(node_id='123', primary_type='ERBS'), Mock(node_id='131', primary_type='RADIONODE'),
                 Mock(node_id='111', primary_type='TCU02'), Mock(node_id='421', primary_type='EPG')]
        self.profile.STATS_UNSUPPORTED_NODE_TYPES = ["TCU02", "SIU02", "EPG", "vEPG", "WMG", "vWMG"]
        self.profile.deallocate_stats_unsupported_nodes(nodes)
        self.assertTrue(mock_update_profile_persistence_nodes_list.called)

    @patch("enmutils_int.lib.workload.pm_06.PM_06.update_profile_persistence_nodes_list")
    def test_deallocate_stats_unsupported_nodes__if_exclusive_nodes_are_not_exist(
            self, mock_update_profile_persistence_nodes_list):
        nodes = [Mock(node_id='123', primary_type='ERBS'), Mock(node_id='131', primary_type='RADIONODE')]
        self.profile.STATS_UNSUPPORTED_NODE_TYPES = ["TCU02", "SIU02", "EPG", "vEPG", "WMG", "vWMG"]
        self.profile.deallocate_stats_unsupported_nodes(nodes)
        self.assertTrue(mock_update_profile_persistence_nodes_list.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
