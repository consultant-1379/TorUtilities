# ********************************************************************
# Name    : Persistence
# Summary : Provides functionality to interact with and manage Redis
#           directly, retrieve databases, set, get, query, and remove.
#           Also includes functionality to pickle and unpickle
#           objects and functions.
# ********************************************************************

import os
import copy_reg
import cPickle as pickle
import pkgutil
import time
import string
import random
import redis
from redis.exceptions import ConnectionError, TimeoutError

import multitasking
import config
import log
import exception
import shell
import mutexer
import filesystem
import process

ENMUTILS_PATH = pkgutil.get_loader('enmutils').filename
EXTERNAL_SOURCES_DIR = os.path.join(ENMUTILS_PATH, 'external_sources')

MUTEX_DB_INDEX = 32
INDEX_MGR_DB_INDEX = 33
NODE_POOL_DB_INDEX = 34
ENMUTILS_DB_PORT = 6379

pid = None


class Persistence(object):

    def __init__(self, index):
        """
        Constructor for a Persistence object.

        :param index: redis db index
        :type index: int
        """

        self.port = ENMUTILS_DB_PORT
        self.daemon_started = False
        self.server_db_name = "enmutils-db-{0}".format(self.port)
        self.server_db_dir = os.path.realpath(os.path.join(EXTERNAL_SOURCES_DIR, "db"))
        self.server_db_path = os.path.join(self.server_db_dir, "enmutils-db")
        self.server_db_conf_path = os.path.join(self.server_db_dir, "enmutils-db.conf")
        self.server_dir = '/var/db/enmutils'
        self.server_cli_path = os.path.join(self.server_db_dir, "redis-cli")
        self.connection = None
        self.index = index
        self.environ = config.get_environ()  # local, jenkins, testing, production
        self.production = self.environ in ["testing", "production"]
        self.logging_enabled = log.logger is not None
        self.db_daemon = None

    def establish_connection(self):
        """
        Establishes the connection to redis or fakeredis depending on the environ setup
        """

        if self.connection:
            return
        if self.production:
            if self.logging_enabled:
                log.logger.debug("Initializing client Redis connection to DB index {0} running on local port {1}"
                                 .format(self.index, self.port))
            self._start_redis_daemon()
            self.connection = redis.StrictRedis(port=self.port, db=self.index)
        else:
            import fakeredis
            self.connection = fakeredis.FakeStrictRedis()

    def _start_redis_daemon(self):
        """
        Starts redis daemon if not running on the deployment
        """

        if self.daemon_started:
            return

        with mutexer.mutex("persistence-start-db"):
            if not self.is_db_running():
                filesystem.create_dir(self.server_dir, log_output=False)

                self.db_daemon = multitasking.UtilitiesExternalDaemon(
                    self.server_db_name,
                    [self.server_db_path, self.server_db_conf_path, "--port {0}".format(self.port)])

                db_pid = self.db_daemon.get_pid()

                if not db_pid:
                    log.logger.debug("Removing PID file: {0}".format(self.db_daemon.pidfile))
                    self.db_daemon.delete_pid_file()
                    self.db_daemon.pid = None

                self.db_daemon.close_all_fds = True
                self.db_daemon.start()
                time.sleep(1)

            self.daemon_started = True

    def set(self, key, value, expiry, log_values=True):
        """
        Values are persisted with a specified expiry time (in seconds), where a negative value denotes no expiry

        :param key: key identifier for the value
        :type key: str
        :param value: object to store
        :type value: object
        :param expiry: Duration of time until the key becomes invalid (seconds). A negitive value indicates no expiry
        :type expiry: int
        :param log_values: Security option to disable writing sensitive values to logs (optional)
        :type log_values: bool (optional)
        :raises ValueError: raises if key is not instance or value is none ot expiry is none
        """
        # Make sure we have sane inputs
        if not isinstance(key, str):
            raise ValueError("Could not persist data; specified key is not of type string")
        elif value is None:
            raise ValueError("Could not persist data; specified value is NoneType")
        elif expiry is None:
            raise ValueError("Could not persist data; specified expiry is NoneType")

        # Print out a message stating what we are going to persist
        if expiry >= 0:
            expiry_string = "expires in %ss" % expiry
        else:
            expiry_string = "never expires"

        if log_values and self.logging_enabled:
            message = "  Persisting %s = %s [%s]" % (key, value, expiry_string)
            end_message = "...(truncated as value is too large)"
            log.logger.debug("%s%s" % (message[:1000], end_message) if len(message) >= 1000 else message)

        # pickle the value before persisting
        value = pickle.dumps(value, pickle.HIGHEST_PROTOCOL)

        if expiry >= 0:
            self.connection.setex(key, expiry, value)
        else:
            self.connection.set(key, value)

    def get(self, key):
        """
        Retrieves a value from persistence using the key as it's identifier

        :param key: cache key
        :type key: str

        :returns: value of the specified key
        :rtype: str or None

        """

        try:
            return pickle.loads(self.connection.get(key))
        except Exception as e:
            if self.has_key(key):
                if self.logging_enabled:
                    log.logger.debug('Error getting key {0}, error was: {1}'.format(key, str(e)))
                strs_in_error = (_ for _ in ["cannot import", "NEWOBJ"] if _ in str(e))
                if key in ["administrator_session", "workload_admin_session"] and any(strs_in_error):
                    if self.logging_enabled:
                        log.logger.debug('Removing key {0}, error was: {1}'.format(key, str(e)))
                    self.remove(key)

    def get_keys(self, keys):
        """
        Retrieves all values from persistence using the keys as identifiers

        :param keys: keys of the values to retrieve
        :type keys: list

        :returns: list of values from the db
        :rtype: list

        """
        values = []

        pipeline = self.connection.pipeline()

        try:
            for key in keys:
                pipeline.get(key)
            values = pipeline.execute()
        except Exception as e:
            if self.logging_enabled:
                log.logger.debug('Error getting keys {0}, error [{1}]'.format(keys, str(e)))
        loaded_objects = []

        for value in values:
            if value:
                try:
                    loaded_objects.append(pickle.loads(value))
                except Exception as e:
                    log.logger.debug("Failed to load object correctly, error encountered: {0}".format(str(e)))
        return loaded_objects

    def has_key(self, key):
        """
        Checks if key exists in storage

        :param key: key to search for
        :type key: str

        :returns: True if the database has the specified key
        :rtype: bool

        """
        try:
            return self.connection.exists(key)
        except (ConnectionError, TimeoutError) as e:
            log.logger.debug("Error connecting to Redis DB: {0}".format(str(e)))
            time.sleep(2)

            if not self.is_db_running():
                self.daemon_started = False

            self.connection = None
            self.establish_connection()

            log.logger.debug("Re-checking if key exists: {0}".format(key))
            return self.has_key(key)

    def is_db_running(self):
        """
        Check if Redis DB is running

        :returns: Boolean to indicate if DB is running or not
        :rtype: bool
        """
        log.logger.debug("Checking if Redis DB is running")
        cmd = shell.Command("%s -p %d ping" % (self.server_cli_path, self.port), log_cmd=False)
        response = shell.run_local_cmd(cmd)
        db_running = True if response.ok else False
        log.logger.debug("Redis DB running (i.e. pong response detected from ping): {0}".format(db_running))
        return db_running

    def remove(self, key):
        """
        Removes key and value from persistence

        :param key: key to remove
        :type key: string

        :returns: 1 if the removal was successful 0 if the key was not found.
        :rtype: int

        """
        result = 0
        try:
            result = self.connection.delete(key)
        except:
            if self.logging_enabled:
                log.logger.debug('Error removing the key %s' % key)
        return result

    def get_ttl(self, key):
        """
        Determines the ttl (time to live), the amount of time before the key expires

        :param key: persisted item's identifier, used to locate the item and check it's ttl
        :type key: string

        :returns: the amount of time before the key expires
        :rtype: int or None if no ttl is found with the specified key

        """
        ttl = None
        try:
            if self.connection.exists(key):
                ttl = self.connection.ttl(key)
        except:
            if self.logging_enabled:
                log.logger.debug('Error getting ttl for key %s' % key)

        return ttl

    def update_ttl(self, key, expiry):
        """
        Updates the ttl (time to live), the amount of time before the key expires

        :param key: persisted item's identifier, used to locate the item in persistence
        :type key: string
        :param expiry: Duration of time until the key becomes invalid (seconds). A negative value indicates no expiry
        :type expiry: int
        """

        try:
            if self.connection.exists(key):
                self.connection.expire(key, expiry)
        except:
            if self.logging_enabled:
                log.logger.debug('Error updating ttl for key %s' % key)

    def get_all_keys(self):
        """
        Returns a list of all keys in storage

        :returns: list of keys
        :rtype: list

        """

        key_list = None

        try:
            key_list = self.connection.keys("*")
        except:
            if self.logging_enabled:
                log.logger.debug('Error getting all keys')

        return key_list

    def clear(self):
        """
        Removes all keys from storage that do not have an infinite expiration

        NOTE: Keys that have no expiration or begin with 'permanent-' will not be cleared
        """

        try:
            keys = self.get_all_keys()
            for key in keys:
                if self.connection.ttl(key) > -1 and not key.startswith("permanent-"):
                    self.remove(key)
        except:
            exception.process_exception("Exception raised while clearing persistence DB")
            raise

        if log.logger is not None:
            log.logger.debug("Persistence cleared successfully [index {0}]".format(self.index))
        else:
            print "Persistence cleared successfully [index {0}]".format(self.index)

    def clear_all(self):
        """
        Removes all keys from storage

        :return: cleared persistance database
        :rtype: None
        """

        result = False

        try:
            result = self.connection.flushdb()
        except:
            exception.process_exception("Exception raised while forcefully clearing persistence DB")
            raise

        if log.logger is not None:
            log.logger.debug("Successfully executed forceful clear of persistence DB [index {0}]".format(self.index))
        else:
            print "Successfully executed forceful clear of persistence DB [index {0}]".format(self.index)

        return result

    def publish(self, channel, msg):
        """
        Publishes the message to the specified channel

        :param channel: Channel to which message will be published
        :type channel: str
        :param msg: Message to be published
        :type msg: str
        """

        self.connection.publish(channel, msg)

    def subscribe(self, channel):
        """
        Subscribes to the specified channel; messages are yielded to the caller

        :param channel: Channel to subscribe to
        :type channel: str
        """
        subscription = self.connection.pubsub()
        subscription.subscribe([channel])

        for msg in subscription.listen():
            if "data" in msg and len(str(msg['data'])) > 1:
                yield str(msg['data'])

    def mutex_pop(self, mutex_identifier, timeout=30, log_output=False):
        """
        Obtains a mutex lock for a specified identifier

        :param mutex_identifier: Identifier to use for the queue name
        :type mutex_identifier: str
        :param timeout: Time to wait (in seconds) for the pop to return
        :type timeout: int
        :param log_output: Boolean to indicate if output should be logged
        :type log_output: bool
        :returns: tuple containing key and val from the mutex
        :rtype: tuple

        """

        pid_string = get_unique_id()
        if log_output:
            log.logger.debug("Using unique value {0} to obtain lock {1}".format(pid_string, mutex_identifier))
        count = 0
        time_delay = 0.2  # seconds to wait between attempts to set the mutex
        log_interval = 30  # seconds to wait between log statements to indicate waiting on mutex
        if timeout:
            timeout *= 1000

        while not self.connection.set(mutex_identifier, pid_string, nx=True, px=timeout):
            time.sleep(time_delay)
            count += 1
            if not count % (log_interval / time_delay):
                self.release_lock_if_holder_not_running(mutex_identifier)

        if log_output:
            process_id = pid_string.split("_")[0].lstrip("pid")
            log.logger.debug(
                "Lock {0} now held by this process id: {1} with lock id: {2}".format(mutex_identifier, process_id,
                                                                                     pid_string))
        return mutex_identifier, pid_string

    def release_lock_if_holder_not_running(self, mutex_identifier):
        """
        Attempts to release the lock if the process holding the lock is no longer running

        :param mutex_identifier: Mutex identifier
        :type mutex_identifier: str
        """
        existing_lock_holder_string = self.connection.get(mutex_identifier)
        if existing_lock_holder_string and existing_lock_holder_string.startswith("pid"):
            pid = existing_lock_holder_string.split('_')[0].replace('pid', '')
            process_name = process.get_process_name(process_id=pid)
            log.logger.debug("Still waiting for lock {0} to be released - currently held by process id: {1} "
                             "with process name: {2} and lock id: {3}".format(mutex_identifier, pid, process_name,
                                                                              existing_lock_holder_string))
            if not process.is_pid_running(pid):
                log.logger.debug("Releasing existing lock so that current process can set new lock")
                self.mutex_push((mutex_identifier, existing_lock_holder_string))

    def mutex_push(self, mutex):  # pragma: no cover
        """
        Does a push of a token value onto the queue linked to the passed identifier}

        :type mutex: tuple
        :param mutex: tuple containing key and val for the mutex
        """

        # This idea stolen from Redlock-py library

        unlock_script = """
                if redis.call("get",KEYS[1]) == ARGV[1] then
                    return redis.call("del",KEYS[1])
                else
                    return 0
                end"""
        try:
            self.connection.eval(unlock_script, 1, mutex[0], mutex[1])
        except Exception as e:
            log.logger.debug('Could not release lock. Reason "%s"' % str(e))

    def _is_expired(self, key):
        """
        Returns True if the persistence object has expired

        :param key: identifier for the persistence object
        :type key: str

        :returns: True if the persistence object has expired
        :rtype: boolean
        """

        return self.connection.get(key) is None

    def save(self):
        """
        Saves a snapshot of the Redis Db at the moment it is issued
        Snapshot stored in location specified under 'dir' in the enmutils-db.conf file

        """
        self.connection.save()

    def shutdown(self):
        """
        Shutdown the Redis process. Stops all persistence
        """

        self.connection.shutdown()

    @classmethod
    def get_db(cls, index):
        """
        classmethod to create a singleton instance of a Database connection for given name, if a connection does not already exist.

        :param index: Database index
        :type index: int

        :returns: Persistence object
        :rtype: Persistence
        """

        index_str = 'db%d' % index

        if index_str not in cls.__dict__:
            db = cls(index=index)
            db.establish_connection()
            setattr(cls, index_str, db)
        return getattr(cls, index_str)


# Below are the helper functions to delegate the persistence operations on the persistence object
# This is for backword compatibility across the api

def get_db(index=None):
    """
    Returns the persistence object if exists otherwise create a new persistence connection

    :param index: Db index
    :type index: int

    :returns: Persistence object (singleton)
    :rtype: Persistence
    """

    return Persistence.get_db(index=index)


def default_db():
    """
    Returns the default pesistence object using the redis db index.

    :returns: default persistence object
    :rtype: Persistence

    """
    return Persistence.get_db(config.get_redis_db_index())


def mutex_db():
    """
    Returns the mutex persistence object.

    :returns: mutex persistence object
    :rtype: Persistence
    """

    return Persistence.get_db(MUTEX_DB_INDEX)


def index_db():
    """
    Returns the index manager persistence object.

    :returns: index manager persistence object
    :rtype: Persistence
    """

    return Persistence.get_db(INDEX_MGR_DB_INDEX)


def node_pool_db():
    """
    Returns the node pool persistence object

    :returns: node pool persistence object
    :rtype: Persistence
    """

    return Persistence.get_db(NODE_POOL_DB_INDEX)


def set(*args, **kwargs):  # pylint: disable=redefined-builtin
    """
    Values are persisted with a specified expiry time (in seconds), where a negative value denotes no expiry

    :param args: An ordered list of arguments required to persist an object, [key, value, expiry], where key (string) is the identifier used to persist the value under, value is the object to persist and expiry (int) is the time in seconds to persist the object for.
    :type args: list
    :param kwargs: A dictionary of optional keyword arguments used in persisting an object, {log_values: True}, where log_values specifies if the persistence of the object is logged
    :type kwargs: dict
    :return: set values in persisted or default datavase
    :rtype: None
    """

    in_mutex_db = mutex_db().has_key(args[0])
    return mutex_db().set(*args, **kwargs) if in_mutex_db else default_db().set(*args, **kwargs)


def get(*args, **kwargs):
    """
    Retrieves a value from either the default or mutex persistence objects using the key as it's identifier

    :param args: An ordered list of arguments required to retrieve a value, [key] key (string) to retrieve the value
    :type args: list
    :param kwargs: The keyword arguments to pass to the method
    :type kwargs: dict

    :return: object from persistence; None if the key doesn't exist
    :rtype: Persistence or None

    """
    return mutex_db().get(*args, **kwargs) or get_from_default_db(*args, **kwargs)


def get_from_default_db(*args, **kwargs):
    """
    Retrieves a value from the default db using the key as it's identifier

    :param args: An ordered list of arguments required to retrieve a value, [key] key (string) to retrieve the value
    :type args: list
    :param kwargs: The keyword arguments to pass to the method
    :type kwargs: dict

    :return: object from persistence; None if the key doesn't exist
    :rtype: Persistence or None

    """
    return default_db().get(*args, **kwargs)


def get_keys(*args, **kwargs):
    """
    Retrieves a list of values from either the default or mutex persistence objects using the keys as identifiers

    :param args: An ordered list of arguments required to retrieve a value, [key] key (string) to retrieve the value
    :type args: list
    :param kwargs: The keyword arguments to pass to the method
    :type kwargs: dict
    :return: object from persistence; [] if none of the keys exist
    :rtype: Persistence or None

    """

    return mutex_db().get_keys(*args, **kwargs) or get_key_values_from_default_db(*args, **kwargs)


def get_key_values_from_default_db(*args, **kwargs):
    """
    Retrieves a list of values from the default db using the keys as identifiers

    :param args: An ordered list of arguments required to retrieve a value, [key] key (string) to retrieve the value
    :type args: list
    :param kwargs: The keyword arguments to pass to the method
    :type kwargs: dict
    :return: list of objects from persistence; [] if none of the keys exist
    :rtype: list
    """
    return default_db().get_keys(*args, **kwargs)


def remove(*args, **kwargs):
    """
    Removes an object from either the default or mutex persistence objects using the key as it's identifier.

    :param args: An ordered list of arguments required to remove an object, [key] key (string) to remove
    :type args: list
    :param kwargs: The keyword arguments to pass to the method
    :type kwargs: dict
    :returns: return code of 1(Success) or 0(Fail)
    :rtype: int

    """
    return default_db().remove(*args, **kwargs) or mutex_db().remove(*args, **kwargs)


def get_ttl(*args, **kwargs):
    """
    Returns the ttl (time to live), the amount of time before the key expires

    :param args: An ordered list of arguments required to return the ttl, [key] key (string) of the persistence object.
    :type args: list
    :param kwargs: The keyword arguments to pass to the method
    :type kwargs: dict
    :returns: the amount of time before the key expires;
    :rtype: int or None

    """
    return default_db().get_ttl(*args, **kwargs)


def update_ttl(*args, **kwargs):
    """
    Updates the ttl (time to live), the amount of time before the key expires

    :param args: An ordered list of arguments required to update the ttl, [key, expiry] key (string) of the persistence object, expiry (int) of the ttl.
    :type args: list
    :param kwargs: The keyword arguments to pass to the method
    :type kwargs: dict
    :return: updated ttl in database
    :rtype: None
    """
    return default_db().update_ttl(*args, **kwargs)


def has_key(key):
    """
    Checks if key exists in either the default or mutex persistence objects

    :param key: The key to search for in either the default or mutex persistence objects
    :type key: str
    :return: True if the database has the specified key
    :rtype: boolean

    """
    return default_db().has_key(key) or mutex_db().has_key(key)


def clear(*args, **kwargs):
    """
    Removes all keys from storage that do not have an infinite expiration.
    NOTE: Keys that have no expiration or begin with 'permanent-' will not be cleared

    :param args: An ordered list of arguments required to check if key exists in either the default or mutex persistence objects, [key] key (string) to search for.
    :type args: list
    :param kwargs: The keyword arguments to pass to the method
    :type kwargs: dict
    :return: cleared specific information in default and mutex database
    :rtype: None

    """
    rc1 = default_db().clear(*args, **kwargs)
    rc2 = mutex_db().clear(*args, **kwargs)
    return rc1 and rc2


def clear_all(*args, **kwargs):
    """
    Removes all keys from storage including those persisted infinitely

    :param args: An ordered list of arguments required to check if key exists in either the default or mutex persistence objects, [key] key (string) to search for.
    :type args: list
    :param kwargs: The keyword arguments to pass to the method
    :type kwargs: dict
    :return: cleared deafault and mutex databse
    :rtype: None

    """
    rc1 = default_db().clear_all(*args, **kwargs)
    rc2 = mutex_db().clear_all(*args, **kwargs)
    return rc1 and rc2


def get_all_keys(*args, **kwargs):
    """
    Returns a list of all keys in the default or mutex persistence objects

    :param args: An ordered list of arguments required to check if key exists in either the default or mutex persistence objects, [key] key (string) to search for.
    :type args: list
    :param kwargs: The keyword arguments to pass to the method
    :type kwargs: dict
    :return: list of keys
    :rtype: list

    """
    log.logger.debug("Fetching list of all key names")
    db_keys = default_db().get_all_keys(*args, **kwargs)
    db_keys.extend(mutex_db().get_all_keys(*args, **kwargs))
    db_keys.sort()
    return db_keys


def get_all_default_keys(*args, **kwargs):
    """
    Returns a list of all keys in the default database

    :param args: An ordered list of arguments required to check if key exists in the default [key] key (string) to
                search for.
    :type args: list
    :param kwargs: The keyword arguments to pass to the method
    :type kwargs: dict

    :return: list of keys
    :rtype: list
    """
    db_keys = default_db().get_all_keys(*args, **kwargs)
    db_keys.sort()
    return db_keys


def publish(*args, **kwargs):
    """
    Publishes the message to the specified channel

    :param args: An ordered list of arguments required to check if key exists in either the default or mutex persistence objects, [key] key (string) to search for.
    :type args: list
    :param kwargs: The keyword arguments to pass to the method
    :type kwargs: dict
    :return: published message to specified channel
    :rtype: None

    """
    return default_db().publish(*args, **kwargs)


def subscribe(*args, **kwargs):
    """
    Subscribes to the specified channel; messages are yielded to the caller

    :param args:An ordered list of arguments required to subscribe to a specified channel,[channel] where channel (string) is the channel to which message will be published, msg (str) message to be published.
    :type args: list
    :param kwargs: The keyword arguments to pass to the method
    :type kwargs: dict
    :return: subscribe to pecified channel
    :rtype: None

    """
    return default_db().subscribe(*args, **kwargs)


def mutex_pop(*args, **kwargs):
    """
    Obtains a mutex lock for a specified identifier

    :param args: An ordered list of arguments required to obtain a mutex lock, [identifier] identifier (string) to use for the queue name.
    :type args: *
    :param kwargs: A dictionary of optional keyword arguments, {timeout:30} where timeout specifies time to wait (in seconds) for the pop to return.
    :type kwargs: *

    :returns: tuple containing key and val from the mutex
    :rtype: tuple

    """
    return mutex_db().mutex_pop(*args, **kwargs)


def mutex_push(*args, **kwargs):
    """
    Returns a mutex lock for the specified identifier

    :param args: An ordered list of arguments required to return a mutex lock for the specified identifier, [mutex](tuple) containing key and val for the mutex
    :type args: *
    :param kwargs: The keyword arguments to pass to the method
    :type kwargs: *

    :return: pushed information to mutex database
    :rtype: None

    """
    return mutex_db().mutex_push(*args, **kwargs)


def _is_expired(*args, **kwargs):
    """
    Returns True if the persistence object has expired

    :param args: An ordered list of arguments required to check if the persistence object has expired, [key] (string) identifier for the persistence object
    :type args: list
    :param kwargs: The keyword arguments to pass to the method
    :type kwargs: dict
    :returns: True if the persistence object has expired
    :rtype: boolean

    """
    return default_db()._is_expired(*args, **kwargs)


def save(*args, **kwargs):
    """
    Saves a snapshot of the Redis Db at the moment it is issued
    Snapshot stored in location specified under 'dir' in the enmutils-db.conf file

    :param args: An ordered list of arguments required to check if the persistence object has expired, [key] (string) identifier for the persistence object
    :type args: list
    :param kwargs: The keyword arguments to pass to the method
    :type kwargs: dict
    :return: saved snapshot of database
    :rtype: None
    """
    return default_db().save(*args, **kwargs)


def shutdown(*args, **kwargs):
    """
    Shutdown the Redis process. Stops all persistence

    :param args: An ordered list of arguments required to check if the persistence object has expired, [key] (string) identifier for the persistence object
    :type args: list
    :param kwargs: The keyword arguments to pass to the method
    :type kwargs: dict
    :return: stopped database info
    :rtype: None
    """
    return default_db().shutdown(*args, **kwargs)


def get_unique_id():
    """
    Generates a random id
    :returns: random id
    :rtype: str
    """
    CHARACTERS = string.ascii_letters + string.digits
    pid = os.getpid()
    random_id = ''.join(random.choice(CHARACTERS) for _ in range(13))
    return "pid{0}_{1}".format(pid, random_id)


class picklable_boundmethod(object):
    def __init__(self, method):
        self.method = method

    def __getstate__(self):
        return self.method.im_self, self.method.im_func.__name__

    def __setstate__(self, (s, fn)):
        self.method = getattr(s, fn)

    def __call__(self, *args, **kwargs):
        return self.method(*args, **kwargs)


def pickle_obj_state(inst_state):
    kwargs = inst_state.__dict__
    klass = inst_state.__class__
    return unpickle_obj_state, (klass, kwargs)


def unpickle_obj_state(klass, kwargs):
    if hasattr(klass, 'REPLACE_CLASS'):
        klass = klass.REPLACE_CLASS
    return klass(**kwargs)


def persistable(klass):
    copy_reg.pickle(klass, pickle_obj_state)
    return klass
