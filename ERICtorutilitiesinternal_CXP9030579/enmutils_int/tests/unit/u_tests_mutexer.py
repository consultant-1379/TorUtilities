#!/usr/bin/env python

import unittest2
from enmutils.lib import mutexer

from mock import patch
from testslib import unit_test_utils


class MutexerUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils.lib.mutexer.persistence')
    @patch('enmutils.lib.mutexer.release_mutex')
    @patch('enmutils.lib.mutexer.acquire_mutex')
    def test_mutex__using_local_mutex_does_not_raise_exception(self, mock_acquire, mock_release, *_):
        with mutexer.mutex("process-exception"):
            self.assertEqual(mock_acquire.call_count, 1)
        self.assertEqual(mock_release.call_count, 1)

    @patch('enmutils.lib.mutexer.persistence')
    @patch("enmutils.lib.mutexer.log")
    @patch('enmutils.lib.mutexer.remove_mutex_key_from_cache')
    @patch('enmutils.lib.mutexer.add_mutex_key_to_cache')
    def test_mutex__using_persisted_mutex_does_not_raise_exception(
            self, mock_add_mutex_key_to_cache, mock_remove_mutex_key_from_cache, mock_log, *_):
        with mutexer.mutex("mutex-persisted-data", persisted=True, log_output=False):
            self.assertEqual(mock_add_mutex_key_to_cache.call_count, 1)
        self.assertEqual(mock_remove_mutex_key_from_cache.call_count, 1)
        self.assertFalse(mock_log.logger.debug.called)

    @patch('enmutils.lib.mutexer.persistence')
    @patch("enmutils.lib.mutexer.log")
    @patch('enmutils.lib.mutexer.remove_mutex_key_from_cache')
    @patch('enmutils.lib.mutexer.add_mutex_key_to_cache')
    def test_mutex__using_persisted_mutex_calls_debug_command_if_logging_enabled(
            self, mock_add_mutex_key_to_cache, mock_remove_mutex_key_from_cache, mock_log, *_):
        with mutexer.mutex("mutex-persisted-data", persisted=True, log_output=True):
            self.assertEqual(mock_add_mutex_key_to_cache.call_count, 1)
        self.assertEqual(mock_remove_mutex_key_from_cache.call_count, 1)
        self.assertEqual(mock_log.logger.debug.call_count, 2)

    @patch('enmutils.lib.mutexer.persistence')
    @patch("enmutils.lib.mutexer.log")
    @patch('enmutils.lib.mutexer.release_mutex')
    @patch('enmutils.lib.mutexer.acquire_mutex')
    def test_mutex__raises_exception_if_acquire_encounters_problem(self, mock_acquire, mock_release, mock_log, *_):
        mock_acquire.side_effect = Exception
        with self.assertRaises(BaseException):
            with mutexer.mutex("process-exception"):
                self.assertEqual(mock_acquire.call_count, 1)
        self.assertEqual(mock_release.call_count, 1)
        self.assertTrue(mock_log.logger.debug.called)

    @patch("enmutils.lib.mutexer.cache.get")
    @patch("enmutils.lib.mutexer.cache.has_key")
    def test_add_mutex_key_to_cache__success(self, mock_has_key, mock_get):
        mock_has_key.return_value = True
        mutexer.add_mutex_key_to_cache([1, 2])
        self.assertTrue(mock_get.called)

    @patch("enmutils.lib.mutexer.cache.get")
    @patch("enmutils.lib.mutexer.cache.has_key")
    def test_add_mutex_key_to_cache__not_success(self, mock_has_key, mock_get):
        mock_has_key.return_value = False
        mutexer.add_mutex_key_to_cache([1, 2])
        self.assertFalse(mock_get.called)

    @patch("enmutils.lib.mutexer.cache.get")
    @patch("enmutils.lib.mutexer.cache.set")
    def test_remove_mutex_key_from_cache__key_not_in_cached(self, mock_set, mock_get):
        mock_get.return_value = [1, 2]
        mutexer.remove_mutex_key_from_cache(3)
        mock_set.assert_called_with('persistence-backed-mutex-keys', [1, 2])

    @patch("enmutils.lib.mutexer.cache.get")
    @patch("enmutils.lib.mutexer.cache.set")
    def test_remove_mutex_key_from_cache__success(self, mock_set, mock_get):
        mock_get.return_value = [1, 2]
        mutexer.remove_mutex_key_from_cache(1)
        mock_set.assert_called_with('persistence-backed-mutex-keys', [2])

    @patch("enmutils.lib.mutexer.cache.get")
    @patch("enmutils.lib.mutexer.cache.set")
    def test_terminate_mutexes__success(self, mock_set, mock_get):
        mock_get.return_value = ["1", "2"]
        mutexer.terminate_mutexes()
        self.assertTrue(mock_set.called)

    @patch("enmutils.lib.mutexer.cache.get")
    @patch("enmutils.lib.mutexer.cache.set")
    def test_terminate_mutexes__not_success(self, mock_set, mock_get):
        mock_get.return_value = []
        mutexer.terminate_mutexes()
        self.assertFalse(mock_set.called)

    @patch("enmutils.lib.mutexer.cache.get")
    @patch("enmutils.lib.mutexer.cache.set")
    def test_acquire_mutex__success(self, mock_set, mock_get):
        mock_get.return_value = None
        mutexer.acquire_mutex("1")
        self.assertTrue(mock_set.called)

    @patch("enmutils.lib.mutexer.threading")
    @patch("enmutils.lib.mutexer.cache.get")
    @patch("enmutils.lib.mutexer.cache.set")
    def test_acquire_mutex__mutex_is_not_none(self, mock_set, *_):
        mutexer.acquire_mutex("1")
        self.assertEqual(mock_set.call_count, 1)

    @patch("enmutils.lib.mutexer.threading")
    @patch("enmutils.lib.mutexer.exception.process_exception")
    @patch("enmutils.lib.mutexer.cache")
    def test_release_mutex__not_success(self, mock_cache, mock_exception, _):
        mock_cache.get.return_value.release.side_effect = Exception
        mutexer.release_mutex("1")
        self.assertTrue(mock_exception.called)

    @patch("enmutils.lib.mutexer.threading")
    @patch("enmutils.lib.mutexer.exception.process_exception")
    @patch("enmutils.lib.mutexer.cache")
    def test_release_mutex__mutexer_none(self, mock_cache, mock_exception, _):
        mock_cache.get.return_value = None
        mutexer.release_mutex("1")
        self.assertFalse(mock_exception.called)

    @patch("enmutils.lib.mutexer.threading")
    @patch("enmutils.lib.mutexer.cache")
    def test_release_mutex__success(self, mock_cache, _):
        mutexer.release_mutex("1")
        self.assertTrue(mock_cache.set.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
