#!/usr/bin/env python
import unittest2
from enmutils_int.lib import cache_int
from mock import patch
from testslib import unit_test_utils


class CacheIntUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.cache_int.CACHE_TTL_MUTEX", None)
    @patch("enmutils_int.lib.cache_int.CACHE_TTL_DICT", None)
    @patch("enmutils_int.lib.cache_int.threading.Lock")
    @patch("enmutils_int.lib.cache_int.ExpiringDict")
    def test_initialize_ttl_cache__successful(self, mock_expiring_dict, mock_lock):
        cache_int.initialize_ttl_cache()
        self.assertEqual(cache_int.CACHE_TTL_MUTEX, mock_lock.return_value)
        self.assertEqual(cache_int.CACHE_TTL_DICT, mock_expiring_dict.return_value)
        mock_expiring_dict.assert_called_with(max_len=500, max_age_seconds=60)

    @patch("enmutils_int.lib.cache_int.CACHE_TTL_DICT", {"ENM_URL": "some_enm_value"})
    @patch("enmutils_int.lib.cache_int.initialize_ttl_cache")
    def test_get_ttl__successful_if_cache_key_already_set(self, mock_initialize_ttl_cache):
        self.assertEqual("some_enm_value", cache_int.get_ttl("ENM_URL"))
        self.assertFalse(mock_initialize_ttl_cache.called)

    @patch("enmutils_int.lib.cache_int.CACHE_TTL_DICT", None)
    @patch("enmutils_int.lib.cache_int.initialize_ttl_cache",
           side_effect=lambda: setattr(cache_int, 'CACHE_TTL_DICT', {"ENM_URL": "some_enm_value"}))
    def test_get_ttl__successful_if_cache_key_not_set(self, mock_initialize_ttl_cache, *_):
        self.assertEqual("some_enm_value", cache_int.get_ttl("ENM_URL"))
        self.assertTrue(mock_initialize_ttl_cache.called)

    @patch("enmutils_int.lib.cache_int.CACHE_TTL_DICT", None)
    @patch("enmutils_int.lib.cache_int.CACHE_TTL_MUTEX")
    @patch("enmutils_int.lib.cache_int.initialize_ttl_cache",
           side_effect=lambda: setattr(cache_int, 'CACHE_TTL_DICT', {}))
    def test_set_ttl__successful_if_cache_not_initialized(self, mock_initialize_ttl_cache, mock_cache_ttl_mutex, *_):
        cache_int.set_ttl("ENM_URL", "some_enm_value")
        self.assertTrue(mock_initialize_ttl_cache.called)
        self.assertTrue(mock_cache_ttl_mutex.acquire.called)
        self.assertEqual(cache_int.CACHE_TTL_DICT, {"ENM_URL": "some_enm_value"})
        self.assertTrue(mock_cache_ttl_mutex.release.called)

    @patch("enmutils_int.lib.cache_int.CACHE_TTL_DICT")
    @patch("enmutils_int.lib.cache_int.CACHE_TTL_MUTEX")
    @patch("enmutils_int.lib.cache_int.initialize_ttl_cache")
    def test_set_ttl__successful_if_cache_initialized(
            self, mock_initialize_ttl_cache, mock_cache_ttl_mutex, mock_cache_ttl_dict, *_):
        cache_int.set_ttl("ENM_URL", "some_enm_value")
        self.assertFalse(mock_initialize_ttl_cache.called)
        self.assertTrue(mock_cache_ttl_mutex.acquire.called)
        mock_cache_ttl_dict.__setitem__.assert_called_with("ENM_URL", "some_enm_value")
        self.assertTrue(mock_cache_ttl_mutex.release.called)

if __name__ == "__main__":
    unittest2.main(verbosity=2)
