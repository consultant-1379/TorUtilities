#!/usr/bin/env python
import time
import pickle

import unittest2
from mock import patch, Mock, MagicMock

from enmutils.lib.persistence import persistable, publish, subscribe
from enmutils.lib import persistence
from testslib import unit_test_utils
from redis.exceptions import ConnectionError


class PersistenceLibUnitTests(unittest2.TestCase):

    def setUp(self):
        self._test_key = "test_key"
        self._test_value = "test_value"

        unit_test_utils.setup()

    def tearDown(self):
        self.close_db()
        unit_test_utils.tear_down()

    def close_db(self):
        persistence.clear_all()

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    def test_has_key__is_successful(self, _):
        db = persistence.Persistence(999)
        mock_connection = Mock()
        mock_connection.exists.return_value = True
        db.connection = mock_connection
        self.assertTrue(db.has_key("some_key"))
        mock_connection.exists.assert_called_with("some_key")

    @patch("enmutils.lib.persistence.time.sleep")
    @patch("enmutils.lib.persistence.Persistence.is_db_running", return_value=True)
    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.Persistence.establish_connection")
    def test_has_key__encounters_transient_connectionerror_where_db_is_still_running(
            self, mock_establish_connection, *_):
        db = persistence.Persistence(999)
        db.daemon_started = True
        mock_original_connection = Mock()
        mock_new_connection = Mock()

        mock_original_connection.exists.side_effect = [ConnectionError, True]
        db.connection = mock_original_connection

        def _update_db_connection_info():
            db.connection = mock_new_connection
        mock_establish_connection.side_effect = _update_db_connection_info

        self.assertTrue(db.has_key("some_key"))

        mock_original_connection.exists.assert_called_with("some_key")
        self.assertTrue(mock_original_connection.exists.call_count == 1)
        mock_new_connection.exists.assert_called_with("some_key")
        self.assertTrue(mock_new_connection.exists.call_count == 1)
        self.assertTrue(db.daemon_started)

    @patch("enmutils.lib.persistence.time.sleep")
    @patch("enmutils.lib.persistence.Persistence.is_db_running", return_value=False)
    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.Persistence.establish_connection")
    def test_has_key__encounters_connectionerror_where_db_is_not_running(self, mock_establish_connection, *_):
        db = persistence.Persistence(999)
        db.daemon_started = True
        mock_original_connection = Mock()
        mock_new_connection = Mock()

        mock_original_connection.exists.side_effect = [ConnectionError, True]
        db.connection = mock_original_connection

        def _update_db_connection_info():
            db.connection = mock_new_connection
        mock_establish_connection.side_effect = _update_db_connection_info

        self.assertTrue(db.has_key("some_key"))

        mock_original_connection.exists.assert_called_with("some_key")
        self.assertTrue(mock_original_connection.exists.call_count == 1)
        mock_new_connection.exists.assert_called_with("some_key")
        self.assertTrue(mock_new_connection.exists.call_count == 1)
        self.assertFalse(db.daemon_started)

    @patch("enmutils.lib.shell.Command")
    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.shell.run_local_cmd")
    def test_is_db_running__returns_true_if_db_running(self, mock_run_local_cmd, *_):
        db = persistence.Persistence(999)
        db.server_cli_path = "some_path"
        db.port = 12345
        db.logging_enabled = True
        mock_run_local_cmd.return_value.ok = 1
        self.assertTrue(db.is_db_running())

    @patch("enmutils.lib.shell.Command")
    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.shell.run_local_cmd")
    def test_is_db_running__returns_false_if_db_not_running(self, mock_run_local_cmd, *_):
        db = persistence.Persistence(999)
        db.server_cli_path = "some_path"
        db.port = 12345
        db.logging_enabled = True
        mock_run_local_cmd.return_value.ok = 0
        self.assertFalse(db.is_db_running())

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    def test_establish_connection__does_nothing_if_connection_set(self, *_):
        db = persistence.Persistence(999)
        mock_connection = Mock()
        db.connection = mock_connection

        db.establish_connection()

        self.assertEqual(db.connection, mock_connection)

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.Persistence._start_redis_daemon")
    @patch("enmutils.lib.persistence.redis.StrictRedis")
    def test_establish_connection__is_successful_in_production_without_logging(self, mock_strictredis, *_):
        db = persistence.Persistence(999)
        db.connection = None
        db.production = True
        db.logging_enabled = False
        db.port = 9999
        db.index = 111

        db.establish_connection()

        self.assertEqual(db.connection, mock_strictredis.return_value)
        mock_strictredis.assert_called_with(port=9999, db=111)

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.Persistence._start_redis_daemon")
    @patch("enmutils.lib.persistence.redis.StrictRedis")
    @patch("enmutils.lib.persistence.log.logger.debug")
    def test_establish_connection__is_successful_in_production_with_logging(self, mock_debug, mock_strictredis, *_):
        db = persistence.Persistence(999)
        db.connection = None
        db.production = True
        db.logging_enabled = True
        db.port = 9999
        db.index = 111

        db.establish_connection()

        self.assertEqual(db.connection, mock_strictredis.return_value)
        mock_strictredis.assert_called_with(port=9999, db=111)
        self.assertEqual(mock_debug.call_count, 1)

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("fakeredis.FakeStrictRedis")
    def test_establish_connection__is_successful_in_test(self, mock_fakestrictredis, *_):
        db = persistence.Persistence(999)
        db.connection = None
        db.production = False

        db.establish_connection()

        self.assertEqual(db.connection, mock_fakestrictredis.return_value)
        self.assertEqual(mock_fakestrictredis.call_count, 1)

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.mutexer.mutex")
    def test_start_redis_daemon__doesnt_do_anything_if_daemon_started_is_set(self, mock_mutex, *_):
        db = persistence.Persistence(999)
        db.daemon_started = True

        db._start_redis_daemon()

        self.assertFalse(mock_mutex.called)

    @patch("enmutils.lib.persistence.Persistence.is_db_running", return_value=True)
    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.filesystem.create_dir")
    @patch("enmutils.lib.persistence.mutexer.mutex")
    def test_start_redis_daemon__doesnt_do_anything_if_daemon_already_running(self, mock_mutex, mock_create_dir, *_):
        db = persistence.Persistence(999)
        db.daemon_started = False

        db._start_redis_daemon()

        self.assertTrue(mock_mutex.called)
        self.assertFalse(mock_create_dir.called)
        self.assertTrue(db.daemon_started)

    @patch("enmutils.lib.persistence.Persistence.is_db_running", return_value=False)
    @patch("enmutils.lib.persistence.time.sleep")
    @patch("enmutils.lib.persistence.filesystem")
    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.multitasking.UtilitiesExternalDaemon")
    @patch("enmutils.lib.persistence.mutexer.mutex")
    def test_start_redis_daemon__starts_daemon_if_was_never_started(self, mock_mutex, mock_daemon, *_):
        db = persistence.Persistence(999)
        db.daemon_started = False
        db.server_dir = "some_dir"
        db.server_db_name = "some_name"
        db.server_db_path = "some_path"
        db.server_db_conf_path = "some_conf_path"
        db.port = "555"
        mock_daemon.return_value.get_pid.return_value = None

        db._start_redis_daemon()

        mock_mutex.assert_called_with("persistence-start-db")
        mock_daemon.assert_called_with("some_name", ["some_path", "some_conf_path", "--port 555"])
        self.assertTrue(mock_daemon.return_value.delete_pid_file.called)
        self.assertTrue(mock_daemon.return_value.start.called)
        self.assertTrue(db.daemon_started)

    @patch("enmutils.lib.persistence.Persistence.is_db_running", return_value=False)
    @patch("enmutils.lib.persistence.time.sleep")
    @patch("enmutils.lib.persistence.filesystem")
    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.multitasking.UtilitiesExternalDaemon")
    @patch("enmutils.lib.persistence.mutexer.mutex")
    def test_start_redis_daemon__starts_daemon_if_was_stopped(self, mock_mutex, mock_daemon, *_):
        db = persistence.Persistence(999)
        db.daemon_started = False
        db.server_dir = "some_dir"
        db.server_db_name = "some_name"
        db.server_db_path = "some_path"
        db.server_db_conf_path = "some_conf_path"
        db.port = "555"
        mock_daemon.return_value.get_pid.return_value = 12345

        db._start_redis_daemon()

        mock_mutex.assert_called_with("persistence-start-db")
        mock_daemon.assert_called_with("some_name", ["some_path", "some_conf_path", "--port 555"])
        self.assertFalse(mock_daemon.return_value.delete_pid_file.called)
        self.assertTrue(mock_daemon.return_value.start.called)
        self.assertTrue(db.daemon_started)

    def test_save_to_storage(self):
        persistence.set(self._test_key, self._test_value, 10)

        if not persistence.has_key(self._test_key):
            self.fail("Key was not found in storage after persisting")

    def test_retrieve_from_storage(self):
        persistence.set(self._test_key, self._test_value, 10)
        result = persistence.get(self._test_key)
        if result != self._test_value:
            self.fail("Key was not retrieved from storage after persisting")

    def test_key_is_expired(self):
        persistence.set(self._test_key, self._test_value, 0.001)
        time.sleep(0.002)
        self.assertTrue(persistence._is_expired(self._test_key))

    def test_key_is_not_expired(self):
        persistence.set(self._test_key, self._test_value, 10)
        self.assertFalse(persistence._is_expired(self._test_key))

    def test_integer_type_key_raises_value_error(self):
        self.assertRaises(ValueError, persistence.set, 123, self._test_value, 0)

    def test_nonetype_key_raises_value_error(self):
        self.assertRaises(ValueError, persistence.set, None, self._test_value, 0)

    def test_nonetype_expiry_raises_value_error(self):
        self.assertRaises(ValueError, persistence.set, self._test_key, self._test_value, None)

    def test_remove_key_also_removes_expiration_key(self):
        persistence.set(self._test_key, self._test_value, 10)
        persistence.remove(self._test_key)
        expiration_key = self._test_key + "-expiry"
        self.assertFalse(persistence.has_key(expiration_key))

    def test_getting_non_existant_key(self):
        self.assertEqual(None, persistence.get(self._test_key))

    def test_function_get_list_of_keys(self):
        persistence.set(self._test_key + "1", self._test_value, 2)
        persistence.set(self._test_key + "2", self._test_value, 2)
        persistence.set(self._test_key + "3", self._test_value, 2)
        key_list = set(persistence.get_all_keys())

        if len(key_list) != 3:
            self.fail("Actual length of key list returned, " + str(len(key_list)) + " did not equal expected length of 3")

    def test_setting_identical_keys_are_overwritten(self):
        persistence.set(self._test_key, self._test_value + "1", 20)
        persistence.set(self._test_key, self._test_value + "2", 30)
        persistence.set(self._test_key, self._test_value + "3", 15)
        self.assertEqual(persistence.get(self._test_key), self._test_value + "3")

    def test_clear_function_does_not_remove_infinite_keys(self):
        # Persist an infinite and a non-infinite key
        persistence.set("perm_key", "perm", -1)
        persistence.set("temp_key", "temp", 5)

        # Clear all non-infinite keys
        persistence.clear()

        # Check that the temp key was removed but the perm key was not
        self.assertTrue(len(set(persistence.get_all_keys())) == 1)

        # Remove the infinite key explicitly
        persistence.remove("perm_key")

        # Check that we have no keys now
        self.assertTrue(len(persistence.get_all_keys()) == 0)

    def test_clear_function_with_no_keys_in_persistence_runs_without_error(self):
        self.assertTrue(len(persistence.get_all_keys()) == 0)
        persistence.clear()
        self.assertTrue(len(persistence.get_all_keys()) == 0)

    def test_setting_a_nonetype_value_raises_error(self):
        self.assertRaises(ValueError, persistence.set, self._test_key, None, 0)

    def test_persistable_responds_with_new_attrs(self):
        t = Test()
        dumped = pickle.dumps(t)
        Test.__init__ = get_new_init(a=1, b=2)
        loaded = pickle.loads(dumped)
        self.assertEqual(loaded.b, 2)

    def test_persistable_replaces_class_for_persisted_object(self):
        t = Test2()
        dumped = pickle.dumps(t)
        loaded = pickle.loads(dumped)
        self.assertTrue(isinstance(loaded, Test2v2))

    @patch('cPickle.loads')
    def test_get_keys(self, *_):
        per = persistence.Persistence(0)
        per.logging_enabled = True
        per.connection = Mock()
        per.connection.pipeline.return_value.execute.return_value = [Mock(), None]
        per.get_keys(["KEY01", "KEY02"])

    @patch('cPickle.loads', side_effect=Exception("Load Failed"))
    @patch('enmutils.lib.log.logger.debug')
    def test_get_keys_log_exception(self, mock_debug, *_):
        per = persistence.Persistence(0)
        per.logging_enabled = True
        per.connection = Mock()
        per.connection.pipeline.return_value.execute.side_effect = Exception("Exception")
        per.get_keys(["KEY01", "KEY02"])
        per.logging_enabled = False
        per.connection = Mock()
        per.connection.pipeline.return_value.execute.side_effect = Exception("Exception")
        per.get_keys(["KEY01", "KEY02"])
        self.assertEqual(mock_debug.call_count, 1)
        per.logging_enabled = False
        per.connection = Mock()
        per.connection.pipeline.return_value.execute.return_value = [Mock(), Mock()]
        per.get_keys(["KEY01", "KEY02"])
        self.assertEqual(mock_debug.call_count, 3)

    @patch('cPickle.loads', side_effect=Exception("NEWOBJ class argument isn't a type object"))
    @patch('enmutils.lib.persistence.Persistence.has_key', return_value=True)
    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils.lib.persistence.Persistence.remove')
    def test_get_removes_unpicklable_admin_key(self, mock_remove, mock_debug, *_):
        key = "administrator_session"
        per = persistence.Persistence(0)
        per.logging_enabled = True
        per.connection = Mock()
        per.connection.get.return_value = "Str"
        self.assertEqual(None, per.get(key))
        self.assertEqual(1, mock_remove.call_count)
        self.assertEqual(2, mock_debug.call_count)

    @patch('cPickle.loads', side_effect=Exception("NEWOBJ class argument isn't a type object"))
    @patch('enmutils.lib.persistence.Persistence.has_key', return_value=True)
    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils.lib.persistence.Persistence.remove')
    def test_get_removes_unpicklable_admin_key__logging_disabled(self, mock_remove, mock_debug, *_):
        key = "administrator_session"
        per = persistence.Persistence(0)
        per.logging_enabled = True
        per.connection = Mock()
        per.logging_enabled = False
        per.connection.get.return_value = "Str"
        self.assertEqual(None, per.get(key))
        self.assertEqual(1, mock_remove.call_count)
        self.assertEqual(0, mock_debug.call_count)

    @patch('cPickle.loads', side_effect=Exception("NEWOBJ class argument isn't a type object"))
    @patch('enmutils.lib.persistence.Persistence.has_key', return_value=True)
    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils.lib.persistence.Persistence.remove')
    def test_get_key(self, mock_remove, mock_debug, *_):
        key = "new_key"
        per = persistence.Persistence(0)
        per.logging_enabled = False
        per.connection = Mock()
        per.connection.get.return_value = "Str"
        self.assertEqual(None, per.get(key))
        self.assertEqual(0, mock_remove.call_count)
        self.assertEqual(0, mock_debug.call_count)

    @patch('cPickle.loads', side_effect=Exception("Exception"))
    @patch('enmutils.lib.persistence.Persistence.has_key', return_value=True)
    @patch('enmutils.lib.log.logger.debug')
    @patch('enmutils.lib.persistence.Persistence.remove')
    def test_get_key_does_not_remove_admin_key_if_not_matched_error_msg(self, mock_remove, mock_debug, *_):
        key = "workload_admin_session"
        per = persistence.Persistence(0)
        per.logging_enabled = False
        per.connection = Mock()
        per.connection.get.return_value = "Str"
        self.assertEqual(None, per.get(key))
        self.assertEqual(0, mock_remove.call_count)
        self.assertEqual(0, mock_debug.call_count)

    @patch('enmutils.lib.persistence.default_db')
    def test_get_all_default_keys__success(self, mock_default_db):
        persistence.get_all_default_keys()
        self.assertEqual(1, mock_default_db.return_value.get_all_keys.call_count)

    @patch('enmutils.lib.persistence.default_db')
    @patch("enmutils.lib.persistence.mutex_db")
    def test_get_keys__is_successful(self, mock_mutex_db, mock_default_db):
        nodes = [Mock()]
        mock_mutex_db.return_value.get_keys.return_value = []
        mock_default_db.return_value.get_keys.return_value = nodes
        self.assertEqual(nodes, persistence.get_keys())

    @patch("enmutils.lib.persistence.get_unique_id", return_value="some_pid_string")
    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.log.logger.debug")
    @patch("enmutils.lib.persistence.time.sleep")
    def test_mutex_pop__is_successful(self, mock_sleep, mock_debug, *_):
        db = persistence.Persistence(10)
        mock_connection = Mock()
        mock_connection.set.side_effect = [False, True]
        db.connection = mock_connection
        self.assertEqual(("some_mutex_id", "some_pid_string"), db.mutex_pop("some_mutex_id"))
        self.assertEqual(mock_sleep.call_count, 1)
        self.assertEqual(mock_debug.call_count, 0)

    @patch("enmutils.lib.persistence.os.getpid")
    @patch("enmutils.lib.persistence.time.sleep")
    @patch("enmutils.lib.persistence.get_unique_id", return_value="pid12345_abcd")
    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.Persistence.release_lock_if_holder_not_running")
    @patch("enmutils.lib.persistence.log.logger.debug")
    def test_mutex_pop__is_successful_if_lock_held_for_long_time(
            self, mock_debug, mock_release_lock_if_holder_not_running, *_):
        db = persistence.Persistence(10)
        count = 30 / 0.2
        mock_connection = Mock()
        mock_connection.set.side_effect = [False] * int(count) + [True]

        db.connection = mock_connection
        self.assertEqual(("some_mutex_id", "pid12345_abcd"), db.mutex_pop("some_mutex_id", log_output=True))
        mock_connection.set.assert_called_with("some_mutex_id", "pid12345_abcd", nx=True, px=30 * 1000)
        self.assertEqual(mock_connection.set.call_count, count + 1)
        self.assertEqual(mock_debug.call_count, 2)
        mock_release_lock_if_holder_not_running.assert_called_with("some_mutex_id")
        self.assertEqual(mock_release_lock_if_holder_not_running.call_count, 1)

    @patch("enmutils.lib.process.get_process_name", return_value="test_process_name")
    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.process.is_pid_running", return_value=False)
    @patch("enmutils.lib.persistence.Persistence.mutex_push")
    @patch("enmutils.lib.persistence.log.logger.debug")
    def test_release_lock_if_holder_not_running__is_successful_if_lock_held_by_other_process_which_is_no_longer_running(
            self, mock_debug, mock_mutex_push, *_):
        db = persistence.Persistence(10)
        mock_connection = Mock()
        existing_lock_string = "pid98765_wxyz"
        mock_connection.get.return_value = existing_lock_string

        db.connection = mock_connection
        db.release_lock_if_holder_not_running("some_mutex_id")

        self.assertEqual(mock_debug.call_count, 2)
        mock_mutex_push.assert_called_with(("some_mutex_id", existing_lock_string))

    @patch("enmutils.lib.process.get_process_name", return_value="test_process_name")
    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.process.is_pid_running", return_value=False)
    @patch("enmutils.lib.persistence.Persistence.mutex_push")
    @patch("enmutils.lib.persistence.log.logger.debug")
    def test_release_lock_if_holder_not_running__is_successful_if_lock_held_by_other_process_but_cant_identify_holder(
            self, mock_debug, mock_mutex_push, *_):
        db = persistence.Persistence(10)
        mock_connection = Mock()
        existing_lock_string = "qwerty"
        mock_connection.get.return_value = existing_lock_string

        db.connection = mock_connection
        db.release_lock_if_holder_not_running("some_mutex_id")

        self.assertEqual(mock_debug.call_count, 0)
        self.assertFalse(mock_mutex_push.called)

    @patch("enmutils.lib.process.get_process_name", return_value="test_process_name")
    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.process.is_pid_running", return_value=False)
    @patch("enmutils.lib.persistence.Persistence.mutex_push")
    @patch("enmutils.lib.persistence.log.logger.debug")
    def test_release_lock_if_holder_not_running__is_successful_if_lock_released_by_time_it_comes_to_read_mutex(
            self, mock_debug, mock_mutex_push, *_):
        db = persistence.Persistence(10)
        mock_connection = Mock()
        mock_connection.get.return_value = None

        db.connection = mock_connection
        db.release_lock_if_holder_not_running("some_mutex_id")

        self.assertEqual(mock_debug.call_count, 0)
        self.assertFalse(mock_mutex_push.called)

    @patch("enmutils.lib.process.get_process_name", return_value="test_process_name")
    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.process.is_pid_running", return_value=True)
    @patch("enmutils.lib.persistence.Persistence.mutex_push")
    @patch("enmutils.lib.persistence.log.logger.debug")
    def test_release_lock_if_holder_not_running__is_successful_if_lock_held_by_other_process_which_is_still_running(
            self, mock_debug, mock_mutex_push, *_):
        db = persistence.Persistence(10)
        mock_connection = Mock()
        existing_lock_string = "pid98765_wxyz"
        mock_connection.get.return_value = existing_lock_string

        db.connection = mock_connection
        db.release_lock_if_holder_not_running("some_mutex_id")

        self.assertEqual(mock_debug.call_count, 1)
        self.assertFalse(mock_mutex_push.called)

    @patch("enmutils.lib.persistence.os.getpid", return_value=12345)
    @patch("enmutils.lib.persistence.random.choice", return_value="a")
    def test_get_unique_id__is_successful(self, *_):
        self.assertEqual("pid12345_aaaaaaaaaaaaa", persistence.get_unique_id())

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    def test_persistence_save__successful(self, _):
        persist = persistence.Persistence(2)
        persist.connection = Mock()
        persist.save()

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    def test_persistence_shutdown__successful(self, _):
        persist = persistence.Persistence(2)
        persist.connection = Mock()
        persist.shutdown()

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.Persistence.get_db")
    def test_index_db__successful(self, *_):
        persistence.index_db()

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.Persistence.get_db")
    def test_get_db__successful(self, *_):
        persistence.get_db()

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.Persistence.get_db")
    def test_node_pool_db__successful(self, *_):
        persistence.node_pool_db()

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.Persistence.get_ttl")
    @patch("enmutils.lib.persistence.default_db", return_value=Mock())
    def test_get_ttl__successful(self, *_):
        persistence.get_ttl(["abc", "bcd"], {"ert": "dewf"})

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.Persistence.update_ttl")
    @patch("enmutils.lib.persistence.default_db", return_value=Mock())
    def test_update_ttl__successful(self, *_):
        persistence.update_ttl(["abc", "bcd"], {"ert": "dewf"})

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.Persistence.mutex_pop")
    @patch("enmutils.lib.persistence.mutex_db", return_value=Mock())
    def test_mutex_pop__successful(self, *_):
        persistence.mutex_pop(["abc", "bcd"], {"ert": "dewf"})

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.Persistence.mutex_push")
    @patch("enmutils.lib.persistence.mutex_db", return_value=Mock())
    def test_mutex_push__successful(self, *_):
        persistence.mutex_push(["abc", "bcd"], {"ert": "dewf"})

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.Persistence.save")
    @patch("enmutils.lib.persistence.default_db", return_value=Mock())
    def test_save__successful(self, *_):
        persistence.save(["abc", "bcd"], {"ert": "dewf"})

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.Persistence.shutdown")
    @patch("enmutils.lib.persistence.default_db", return_value=Mock())
    def test_shutdown__successful(self, *_):
        persistence.shutdown(["abc", "bcd"], {"ert": "dewf"})

    @patch("enmutils.lib.persistence.log.logger.debug")
    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    def test_persistence_remove__add_exception(self, *_):
        persist = persistence.Persistence(2)
        persist.connection = Exception
        persist.logging_enabled = True
        persist.remove("abc")

    @patch("enmutils.lib.persistence.log.logger.debug")
    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    def test_persistence_remove__logging_enabled_false(self, *_):
        persist = persistence.Persistence(2)
        persist.connection = Exception
        persist.logging_enabled = False
        persist.remove("abc")

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    def test_persistence_update_ttl__successful(self, _):
        persist = persistence.Persistence(2)
        persist.connection = Mock()
        persist.logging_enabled = True
        persist.update_ttl("abc", 2)

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    def test_persistence_get_ttl__successful(self, _):
        persist = persistence.Persistence(2)
        persist.connection = Mock()
        persist.logging_enabled = True
        persist.get_ttl("abc")

    @patch("enmutils.lib.persistence.log.logger.debug")
    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    def test_persistence_update_ttl__add_exception(self, *_):
        persist = persistence.Persistence(2)
        persist.connection = Exception
        persist.logging_enabled = True
        persist.update_ttl("abc", 2)

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    def test_persistence_update_ttl__unsuccessful(self, _):
        persist = persistence.Persistence(2)
        persist.connection = ""
        persist.logging_enabled = False
        persist.update_ttl("abc", 2)

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    def test_persistence_publish__successful(self, _):
        persist = persistence.Persistence(2)
        persist.connection = Mock()
        persist.publish("some_channel", "some_msg")

    @patch("enmutils.lib.persistence.log.logger.debug")
    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    def test_persistence_get_ttl__add_exception(self, *_):
        persist = persistence.Persistence(2)
        persist.connection = Exception
        persist.logging_enabled = True
        persist.get_ttl("some_string")

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    def test_persistence_get_ttl__add_exception_condition_false(self, _):
        persist = persistence.Persistence(2)
        persist.connection = Exception
        persist.logging_enabled = False
        persist.get_ttl("abc")

    @patch("enmutils.lib.persistence.log.logger.debug")
    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    def test_persistence_get_all_keys__add_exception(self, *_):
        persist = persistence.Persistence(2)
        persist.connection = Exception
        persist.logging_enabled = True
        persist.get_all_keys()

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    def test_persistence_get_all_keys__add_exception_condition_false(self, _):
        persist = persistence.Persistence(2)
        persist.connection = Exception
        persist.logging_enabled = False
        persist.get_all_keys()

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    def test_persistence_set__logging_enabled_false(self, _):
        persist = persistence.Persistence(2)
        persist.connection = Mock()
        persist.logging_enabled = False
        persist.set("abc", "123", 2, False)

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    def test_persistence_mutex_pop__no_timeout_value(self, _):
        persist = persistence.Persistence(2)
        persist.connection = Mock()
        persist.mutex_pop("abc", None, False)

    def test_init_picklable__value(self):
        pickl = persistence.picklable_boundmethod("method")
        self.assertEqual(pickl.method, "method")

    @patch('enmutils.lib.persistence.picklable_boundmethod.__init__', return_value=None)
    def test_call__picklable_boundmethod(self, _):
        pickl = persistence.picklable_boundmethod("method")
        pickl.method = Mock()
        pickl.__call__(['ab', 'bc'], {'ab': 'abc'})

    @patch('enmutils.lib.persistence.picklable_boundmethod.__init__', return_value=None)
    def test_setstate__picklable_boundmethod(self, _):
        pickl = persistence.picklable_boundmethod("method")
        pickl.method = Mock()
        pickl.__setstate__((Mock(), "some_attribute_name"))

    @patch('enmutils.lib.persistence.picklable_boundmethod.__init__', return_value=None)
    def test_getstate__picklable_boundmethod(self, _):
        pickl = persistence.picklable_boundmethod("method")
        pickl.method = Mock()
        pickl.method.im_func.__name__ = Mock()
        pickl.__getstate__()

    @patch("enmutils.lib.persistence.log.logger.debug")
    @patch('enmutils.lib.persistence.Persistence.__init__', return_value=None)
    def test_persistence_get_ttl__not_exists(self, *_):
        persist = persistence.Persistence(2)
        mock_exist = persist.connection = Mock()
        mock_exist.exists.side_effect = [False]
        persist.get_ttl("some_key")

    @patch("enmutils.lib.persistence.log.logger.debug")
    @patch('enmutils.lib.persistence.Persistence.__init__', return_value=None)
    def test_persistence_update_ttl__not_exists(self, *_):
        persist = persistence.Persistence(2)
        mock_exist = persist.connection = Mock()
        mock_exist.exists.side_effect = [False]
        persist.update_ttl("some_key", 2)

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.exception.process_exception")
    @patch("enmutils.lib.persistence.log.logger.debug")
    def test_clear_all__logger_None(self, *_):
        persistence.log.logger = None
        persist = persistence.Persistence(2)
        with self.assertRaises(Exception):
            persist.clear_all()

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.persistence.exception.process_exception")
    def test_clear__exception(self, *_):
        persist = persistence.Persistence(2)
        with self.assertRaises(Exception):
            persist.clear()

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    @patch("enmutils.lib.exception.process_exception")
    @patch("enmutils.lib.persistence.Persistence.get_all_keys", return_value=[])
    def test_clear__logger_none(self, *_):
        persist = persistence.Persistence(index=999)
        persistence.log.logger = None
        persist.index = 2
        persist.clear()

    @patch("enmutils.lib.persistence.Persistence.get_db", return_value=Mock())
    @patch("enmutils.lib.persistence.default_db")
    def test_publish__success(self, mock_default_db, _):
        persistence.set(self._test_key, self._test_value, 10)
        mock_default_db = MagicMock()
        mock_default_db.publish.return_value = Mock()
        publish("test")

    @patch("enmutils.lib.persistence.Persistence.get_db", return_value=Mock())
    @patch("enmutils.lib.persistence.default_db")
    def test_subscribe__success(self, mock_default_db, _):
        persistence.set(self._test_key, self._test_value, 10)
        mock_default_db = MagicMock()
        mock_default_db.subscribe.return_value = Mock()
        subscribe("test")

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    def test_subscribe_persistence__successful(self, _):
        persist = persistence.Persistence(2)
        persist.connection = MagicMock()
        persist.connection.pubsub.return_value = MagicMock()
        persist.connection.pubsub.return_value.subscribe.return_value = Mock()
        persist.connection.pubsub.return_value.listen.return_value = [{"data": [1, 2]}]
        persist.index = 2
        self.assertEqual(next(persist.subscribe("test")), '[1, 2]')

    @patch("enmutils.lib.persistence.Persistence.__init__", return_value=None)
    def test_subscribe_persistence__successful1(self, _):
        persist = persistence.Persistence(2)
        persist.connection = MagicMock()
        persist.connection.pubsub.return_value = MagicMock()
        persist.connection.pubsub.return_value.subscribe.return_value = Mock()
        persist.connection.pubsub.return_value.listen.return_value = {"hi": 1, "b": 2}
        persist.index = 2
        self.assertRaises(StopIteration, next, persist.subscribe("test"))


def get_new_init(**params):
    def init(inst, **_):
        inst.__dict__.update(**params)
    return init


@persistable
class Test(object):
    def __init__(self, a=1):
        self.a = a


class Test2v2(object):
    def __init__(self, a=1):
        self.a = a


@persistable
class Test2(object):
    REPLACE_CLASS = Test2v2

    def __init__(self, a=1):
        self.a = a


if __name__ == "__main__":
    unittest2.main(verbosity=2)
