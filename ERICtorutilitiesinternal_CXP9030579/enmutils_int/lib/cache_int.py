# ********************************************************************
# Name    : Cache Internal
# Summary : Contains functions to manage Time-to-live in-memory cache
# ********************************************************************

import threading

from expiringdict import ExpiringDict

CACHE_TTL_MUTEX = None
CACHE_TTL_DICT = None
CACHE_TTL_TIME_SECS = 60
CACHE_TTL_MAX_LENGTH = 500


def initialize_ttl_cache():
    """
    Initialize Time-to-live cache (and mutex)
    """
    global CACHE_TTL_MUTEX, CACHE_TTL_DICT
    CACHE_TTL_MUTEX = threading.Lock()
    CACHE_TTL_DICT = ExpiringDict(max_len=CACHE_TTL_MAX_LENGTH, max_age_seconds=CACHE_TTL_TIME_SECS)


def get_ttl(key):
    """
    Get the value of the key within the TTL global dict

    :param key: cache key
    :type key: str
    :return: Value of the key
    :rtype: str
    """

    if not CACHE_TTL_DICT:
        initialize_ttl_cache()
    return CACHE_TTL_DICT.get(key)


def set_ttl(key, value):
    """
    Set the value of the key within TTL cache, i.e. value will expire after set amount of time

    :param key: cache
    :type key: str
    :param value: data to be stored in cache
    :type value: str
    """

    global CACHE_TTL_MUTEX, CACHE_TTL_DICT
    if not CACHE_TTL_DICT or not CACHE_TTL_MUTEX:
        initialize_ttl_cache()
    CACHE_TTL_MUTEX.acquire()
    CACHE_TTL_DICT[key] = value
    CACHE_TTL_MUTEX.release()
