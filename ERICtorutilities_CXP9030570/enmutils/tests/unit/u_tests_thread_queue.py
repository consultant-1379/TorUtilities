#!/usr/bin/env python
import time
import Queue

import unittest2

from enmutils.lib import thread_queue, config
from mock import patch, Mock
from testslib import unit_test_utils


def good_func(interval):
    time.sleep(interval)


def bad_func():
    time.sleep(.001)


class ThreadQueueUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def _sleeper(self, interval):
        time.sleep(interval)

    def test_empty_work_item_list_produces_empty_finished_work_item_list(self):
        self.assertRaises(ValueError, thread_queue.ThreadQueue, [], 3, self._sleeper)

    def test_value_error_raised_when_non_function_given_for_function_reference(self):
        self.assertRaises(ValueError, thread_queue.ThreadQueue, [1, 1], 2, "string")

    def test_value_error_raised_when_given_non_int_num_workers(self):
        self.assertRaises(ValueError, thread_queue.ThreadQueue, [1, 1], "2", self._sleeper)

    @patch("enmutils.lib.thread_queue.ThreadQueue._populate_work_queue")
    @patch("enmutils.lib.thread_queue.ThreadQueue._wait_for_work_to_finish")
    def test_work_items_that_execute_successfully_as_threads_are_marked_as_finished(self, *_):
        tq = thread_queue.ThreadQueue([.01, .02, .03], 3, func_ref=good_func)
        tq.execute()
        for work_item in tq.work_entries:
            self.assertTrue(work_item.finished)

    @patch("enmutils.lib.thread_queue.ThreadQueue._populate_work_queue")
    @patch("enmutils.lib.thread_queue.ThreadQueue._wait_for_work_to_finish")
    def test_work_items_that_dont_execute_successfully_are_still_marked_as_finished(self, *_):
        tq = thread_queue.ThreadQueue([.01, .02, .03], 3, func_ref=bad_func)
        tq.execute()
        for work_item in tq.work_entries:
            self.assertTrue(work_item.finished)

    def test_num_workers_is_adjusted_down_when_work_queue_smaller_than_default_num_workers(self):
        tq = thread_queue.ThreadQueue([1, 2], 4, good_func)
        self.assertEqual(2, tq.num_workers)

    def test_num_workers_is_set_correctly_when_work_queue_larger_than_default_num_workers(self):
        tq = thread_queue.ThreadQueue([1, 2, 3, 4, 5], 2, good_func)
        self.assertEqual(2, tq.num_workers)

    def test_worker_argument_list_is_built_correctly(self):
        tq = thread_queue.ThreadQueue([1, 2], 2, good_func, ["b", 4.3])
        tq._populate_work_queue()
        self.assertEqual([1, "b", 4.3], tq.work_entries[0].arg_list)
        self.assertEqual([2, "b", 4.3], tq.work_entries[1].arg_list)

    def test_worker__completion_level_1(self):
        mock_work_queue = Mock()
        mock_done_queue = Mock()
        mock_work_queue.get.side_effect = [None, Mock(), Queue.Empty]
        mock_done_queue.put.side_effect = Exception
        thread_queue._worker(mock_work_queue, mock_done_queue)

    def test_worker__completion_level_2(self):
        mock_work_queue = Mock()
        mock_done_queue = Mock()
        mock_work_queue.get.side_effect = [None, Mock(), Queue.Empty]
        mock_work_queue.task_done.side_effect = Exception
        thread_queue._worker(mock_work_queue, mock_done_queue)

    @patch("enmutils.lib.multitasking.should_workers_exit")
    @patch("enmutils.lib.thread_queue.log.logger")
    def test_worker__wokers_exit(self, mock_log, mock_should_workers_exit):
        mock_should_workers_exit.side_effect = [False, True]
        mock_log.side_effect = None
        mock_work_queue = Mock()
        mock_done_queue = Mock()
        self.assertEqual(thread_queue._worker(mock_work_queue, mock_done_queue), None)

    @patch("enmutils.lib.multitasking.should_workers_exit")
    @patch("enmutils.lib.thread_queue.log.logger.debug", side_effect=["", "", "", AttributeError])
    def test_worker__wokers_log_logger_Attribute_Error(self, mock_log, mock_should_workers_exit):
        mock_should_workers_exit.side_effect = [True]
        mock_work_queue = Mock()
        mock_done_queue = Mock()
        self.assertEqual(thread_queue._worker(mock_work_queue, mock_done_queue), None)

    @patch("enmutils.lib.thread_queue.Queue")
    def test_populate_work_queue__success(self, mock_queue):
        tq = thread_queue.ThreadQueue([1, 2], 2, good_func, ["b", 4.3])
        tq.additional_args = {"num1": 1, "num2": 2}
        tq._populate_work_queue()
        self.assertEqual([1, {'num1': 1, 'num2': 2}], tq.work_entries[0].arg_list)
        self.assertEqual([2, {'num1': 1, 'num2': 2}], tq.work_entries[1].arg_list)

    @patch("enmutils.lib.thread_queue.Queue")
    def test_populate_work_queue__nosuccess(self, mock_queue):
        tq = thread_queue.ThreadQueue([1, 2], 2, good_func, ["b", 4.3])
        tq.additional_args = ["num1", "num2"]
        mock_obj = Mock()
        mock_obj.empty.return_value = False
        tq.done_queue = mock_obj
        tq._populate_work_queue()
        self.assertEqual([1, 'num1', 'num2'], tq.work_entries[0].arg_list)
        self.assertEqual([2, 'num1', 'num2'], tq.work_entries[1].arg_list)

    @patch("enmutils.lib.thread_queue.Queue")
    def test_populate_work_queue__tuple(self, mock_queue):
        tq = thread_queue.ThreadQueue([1, 2], 2, good_func, ["b", 4.3])
        tq.additional_args = ("num1", "num2")
        tq._populate_work_queue()
        self.assertEqual([1], tq.work_entries[0].arg_list)
        self.assertEqual([2], tq.work_entries[1].arg_list)

    @patch("enmutils.lib.thread_queue.ThreadQueue._populate_work_queue")
    @patch("enmutils.lib.thread_queue.ThreadQueue._wait_for_work_to_finish")
    def test_there_is_no_hang_if_all_worker_threads_die(self, *_):
        tq = thread_queue.ThreadQueue([1, 2, 3, 4, 5, 6, 7], 7, bad_func)
        tq.execute()
        for work_item in tq.work_entries:
            self.assertTrue(work_item.finished)
            self.assertTrue(work_item.exception_raised)

    @patch("enmutils.lib.thread_queue.ThreadQueue._wait_for_work_to_finish")
    def test_done_queue_fills_with_all_work_items_from_work_queue(self, _):
        def test_func(x):
            x = x + 1

        work_items = [x for x in xrange(0, 10)]

        tq = thread_queue.ThreadQueue(work_items, 10, test_func)
        tq.execute()

        self.assertEqual(0, tq.work_queue.qsize())
        self.assertEqual(len(work_items), tq.done_queue.qsize())

    def test_all_work_items_processed_when_some_threads_encounter_exceptions(self):
        def test_func(x):
            if x == 2 or x == 7:
                raise RuntimeError("YIKES!!!")

            x = x + 1

        work_items = [x for x in xrange(0, 10)]

        tq = thread_queue.ThreadQueue(work_items, 10, test_func, task_wait_timeout=0.0001, task_join_timeout=0.0001)
        tq.execute()

        num_exceptions = 0
        num_finished = 0
        for work_item in tq.work_entries:
            if work_item.exception_raised:
                num_exceptions = num_exceptions + 1
            if work_item.finished:
                num_finished = num_finished + 1

        self.assertEqual(2, num_exceptions)
        self.assertEqual(10, num_finished)

    def test_wait_for_done_queue_to_fill_waits_for_a_specified_period_to_assert_if_workers_are_done(self):
        # Set default 'task_wait_timeout' to 3 hours
        config.set_prop("task_wait_timeout", 10800)

        tq = thread_queue.ThreadQueue([5, 7, 10], 3, func_ref=good_func, task_wait_timeout=0.0001,
                                      task_join_timeout=0.0001)
        tq.execute()

        self.assertTrue(float(tq.elapsed_time) < 5.0)

    @patch("enmutils.lib.multitasking.should_workers_exit")
    def test_wait_for_done_queue_to_fill__exit(self, mock_exit):
        mock_exit.return_value = True
        tq = thread_queue.ThreadQueue([5, 7, 10], 3, func_ref=good_func, task_wait_timeout=0.0001,
                                      task_join_timeout=0.0001)
        self.assertEqual(tq._wait_for_done_queue_to_fill(), None)

    @patch("enmutils.lib.thread_queue.ThreadQueue.__init__", return_value=None)
    @patch("enmutils.lib.multitasking.should_workers_exit", return_value=False)
    @patch("enmutils.lib.thread_queue.log.logger.debug")
    def test_wait_for_done_queue_to_fill__break(self, mock_log, *_):
        mock_queue = Mock()
        mock_queue.qsize.return_value = 1
        tq = thread_queue.ThreadQueue([1, 2], 3, func_ref=good_func, task_wait_timeout=1, task_join_timeout=1)
        setattr(tq, 'work_items', [1])
        setattr(tq, 'done_queue', mock_queue)
        setattr(tq, 'task_wait_timeout', 10)
        tq._wait_for_done_queue_to_fill()
        mock_log.assert_called_with("All work items have been processed and moved from work queue to done queue")

    @patch("enmutils.lib.multitasking.get_num_tasks_running")
    def test_wait_for_done_queue_to_fill__loopcounter(self, mock_num_tasks):
        mock_num_tasks.return_value = 0
        tq = thread_queue.ThreadQueue([1, 2], 3, func_ref=good_func, task_wait_timeout=0.0001,
                                      task_join_timeout=0.0001)
        tq.worker_pool = ["1", "2", "3"]
        tq._wait_for_done_queue_to_fill()
        self.assertEqual(tq._wait_for_done_queue_to_fill(), None)

    @patch("enmutils.lib.thread_queue.log.logger.debug")
    def test_execute__no_work_items(self, mock_log):
        tq = thread_queue.ThreadQueue([1, 2], 3, func_ref=good_func, task_wait_timeout=0.0001,
                                      task_join_timeout=0.0001)
        tq.work_items = []
        tq.execute()
        self.assertEqual(1, mock_log.call_count)

    @patch("enmutils.lib.thread_queue.time.sleep")
    @patch("enmutils.lib.timestamp.get_current_time")
    def test_execute__raises_Keyboard_Interrupt(self, mock_current_time, mock_sleep):
        mock_current_time.side_effect = KeyboardInterrupt
        tq = thread_queue.ThreadQueue([5, 7, 10], 3, func_ref=good_func)
        tq.worker_pool = ["1", "2"]
        self.assertRaises(KeyboardInterrupt, tq.execute)
        self.assertTrue(mock_sleep.called)

    def test_process_results__success(self):
        tq = thread_queue.ThreadQueue([5, 7, 10], 3, func_ref=good_func)
        test_number = tq._get_num_successful_results(tq.work_entries)
        test_len = len(tq.work_entries)
        self.assertEqual(tq.process_results(tq.work_entries), (test_number == test_len))

    def test__get_num_successful_results__success(self):
        tq = thread_queue.ThreadQueue([5, 7, 10], 3, func_ref=good_func)
        s = thread_queue.ThreadQueueEntry(tq, tq.work_items)
        t = thread_queue.ThreadQueueEntry(tq, tq.work_items)
        t.result = False
        s.result = True
        test_worker_entries = [t, s]
        self.assertEqual(tq._get_num_successful_results(test_worker_entries), 1)

    @patch('time.sleep')
    @patch('enmutils.lib.thread_queue.ThreadQueue.__init__', return_value=None)
    @patch('enmutils.lib.thread_queue.multitasking.get_num_tasks_running', return_value=3)
    @patch('enmutils.lib.thread_queue.multitasking.join_tasks', return_value=[Mock(), Mock()])
    def test_wait_for_done_queue_to_fill_waits_for_a_specified_period_to_assert_if_workers_are_done__loop(self, *_):
        tq = thread_queue.ThreadQueue()
        tq.work_items = ["abc"]
        tq.task_wait_timeout = 0.1
        tq.done_queue = Mock()
        tq.num_workers = 1
        tq.worker_pool = Mock()
        tq._wait_for_done_queue_to_fill()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
