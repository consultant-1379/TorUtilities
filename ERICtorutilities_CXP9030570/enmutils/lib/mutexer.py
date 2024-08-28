# ********************************************************************
# Name    : Mutexer
# Summary : Provides functionality manage persistened or cached
#           mutexes for locking components.
# ********************************************************************

import threading
from contextlib import contextmanager

import cache
import persistence
import exception
import log

CACHE_KEY = "persistence-backed-mutex-keys"

__cache_lock = threading.RLock()


def add_mutex_key_to_cache(key):
    """
    B{Adds the key of a persistence-backed mutex to the list of keys in cache}

    :type key: tuple
    :param key: tuple containing key and val from the mutex
    """

    if cache.has_key(CACHE_KEY):
        cached_keys = cache.get(CACHE_KEY)
    else:
        cached_keys = []

    cached_keys.append(key)

    cache.set(CACHE_KEY, cached_keys)


def remove_mutex_key_from_cache(key):
    """
    B{Removes the key of a persistence-backed mutex from the list of keys in cache}

    :type key: tuple
    :param key: tuple containing key and val from the mutex
    """

    cached_keys = cache.get(CACHE_KEY)

    if key in cached_keys:
        cached_keys.remove(key)

    cache.set(CACHE_KEY, cached_keys)


def terminate_mutexes():
    """
    B{Terminates all persistence-backed mutexes; to be invoked before exit}
    """

    cached_keys = cache.get(CACHE_KEY)
    if cached_keys:
        for key in cached_keys:
            log.logger.debug("Terminating persistence-backed mutex {0}".format(key))  # pylint: disable=logging-format-interpolation
            persistence.mutex_push(key)

        cache.set(CACHE_KEY, [])


def acquire_mutex(mutex_key):
    """
    B{Acquires the mutex with the specified key}

    :type mutex_key: str
    :param mutex_key: Mutex identifier
    """

    global __cache_lock
    with __cache_lock:
        # Grab the mutex from the cache if it already exists, or create it if it doesn't
        mutex = cache.get(mutex_key)

        if mutex is None:
            mutex = threading.Lock()
            cache.set(mutex_key, mutex)

    # Acquire the mutex
    mutex.acquire()

    with __cache_lock:
        # Store the mutex in the cache
        cache.set(mutex_key, mutex)


def release_mutex(mutex_key):
    """
    B{Releases the mutex of the specified key}

    :type mutex_key: str
    :param mutex_key: Mutex identifier
    """

    with __cache_lock:
        mutex = cache.get(mutex_key)

    # Release the mutex
    if mutex is not None:
        try:
            mutex.release()
        except Exception:
            exception.process_exception(
                "Exception raised during release of mutex: {0}".format(mutex_key))
        else:
            # Store the mutex in the cache
            with __cache_lock:
                cache.set(mutex_key, mutex)


@contextmanager
def mutex(identifier, persisted=False, timeout=30, db=None, log_output=False):
    """
    Context manager mutex generator

    :param identifier: name of the mutex.
    :type identifier: str
    :param persisted: True if the mutex has already been persisted else False.
    :type persisted: bool
    :param timeout: the time to wait (in seconds) for the mutex_pop to return.
    :type timeout: int
    :param db: None or database object to use.
    :type db: database obj
    :param log_output: Boolean flag to indicate whether to log debug output or not
    :type log_output: bool
    :raises BaseException: when BaseException occurs
    :return: yield
    :rtype: yield
    """

    if "mutex" in identifier:
        mutex_key = identifier
    else:
        mutex_key = "mutex-{0}".format(identifier)

    mutex_type = "local" if not persisted else 'persisted'
    mutex = None
    db = db or persistence
    if log_output:
        log.logger.debug("Attempting to acquire {0} mutex key: '{1}'".format(mutex_type, mutex_key))
    try:
        if persisted:
            mutex = db.mutex_pop(mutex_key, timeout=timeout, log_output=log_output)
            add_mutex_key_to_cache(mutex)
        else:
            acquire_mutex(mutex_key)
        yield
    except BaseException as e:
        log.logger.debug("Exception raised during execution of critical area protected by {0} mutex: '{1}' "
                         "- Exception: {2}".format(mutex_type, mutex_key, str(e)))
        raise
    finally:
        if persisted:
            db.mutex_push(mutex)
            remove_mutex_key_from_cache(mutex)
        else:
            release_mutex(mutex_key)

        if log_output:
            log.logger.debug("The {0} mutex key: '{1}' has been released".format(mutex_type, mutex_key))
