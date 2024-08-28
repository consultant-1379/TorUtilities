#!/usr/bin/env python
import sys
from datetime import datetime

import unittest2
from mock import Mock, patch
from parameterizedtestcase import ParameterizedTestCase

from enmutils.lib import persistence as persistence_lib
from enmutilsbin import persistence
from testslib import unit_test_utils


class PersistenceParameterizedTests(ParameterizedTestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.db = Mock()

    def tearDown(self):
        unit_test_utils.tear_down()

    @ParameterizedTestCase.parameterize(
        ("value", "has_key", "assertion"),
        [
            ("bar", True, True),
            (None, True, False),
            ("bar", False, False)
        ]
    )
    def test_get_return_value(self, value, has_key, assertion):
        self.db.has_key.return_value = has_key
        self.db.get.return_value = value
        self.assertEqual(assertion, persistence.get("foo", self.db))

    @ParameterizedTestCase.parameterize(
        ["has_key"],
        [
            [True],
            [False]
        ]
    )
    def test_set_return_value(self, has_key):
        self.db.has_key.return_value = has_key
        self.assertEqual(has_key, persistence.set("abc", "123", 10, self.db))

    @ParameterizedTestCase.parameterize(
        ["has_key"],
        [
            [True],
            [False]
        ]
    )
    def test_remove_return_value(self, has_key):
        self.db.has_key.return_value = has_key
        self.assertEqual((not has_key), persistence.remove("foo", self.db))

    def test_persistence_singleton(self):
        db = persistence_lib.Persistence.get_db(1)
        db2 = persistence_lib.Persistence.get_db(1)
        self.assertEqual(db, db2)

    def test_establish_connection_uses_fake_redis_for_testing(self):
        self.assertTrue(persistence_lib.Persistence.get_db(1).__class__.__name__, 'FakeStrictRedis')

    @patch("enmutilsbin.persistence.init.exit")
    @patch('enmutilsbin.persistence.init')
    @patch('enmutilsbin.persistence.set')
    @patch("enmutilsbin.persistence.exception.handle_exception", return_value=None)
    @patch('enmutils.lib.persistence.Persistence.has_key')
    @patch("enmutilsbin.persistence.exception.handle_invalid_argument")
    @ParameterizedTestCase.parameterize(
        ("sys_argv", "assert_value", 'mock_has_key'),
        [
            (["persistence", "set", "key", "some_value", 'c'], True, False),
            (["persistence", "set", "key", "some_value", '1'], False, False),
            (["persistence", "set", "key", "some_value", 'InDeFiNiTe'], False, False),
            (['persistence', 'remove', 'foo'], True, False),
            (['persistence', 'remove', 'foo'], False, True),
        ]
    )
    def test_handle_exception_is_called_when_expiry_not_int(self, sys_argv, assert_value, mock_has_key,
                                                            mock_handle_invalid_argument, mock_persistence_has_key, *_):
        sys.argv = sys_argv
        mock_persistence_has_key.return_value = mock_has_key
        persistence.cli()
        self.assertEqual(mock_handle_invalid_argument.called, assert_value)

    @patch("enmutils.lib.init.exit")
    @patch("enmutils.lib.persistence.Persistence.save")
    @patch("enmutils.lib.init.global_init")
    @patch("enmutils.lib.filesystem.copy")
    @patch("enmutils.lib.filesystem.create_dir")
    @patch("enmutils.lib.filesystem.remove_dir")
    @patch("enmutils.lib.log.logger.info")
    def test_persistence_backup(self, mock_log_info, *_):
        sys.argv = ["persistence", "backup"]
        persistence.cli()
        self.assertTrue(mock_log_info.call_count == 1)

    @patch("enmutils.lib.init.exit")
    @patch("enmutils.lib.persistence.default_db")
    @patch("enmutils.lib.persistence.Persistence.shutdown")
    @patch("enmutils.lib.init.global_init")
    @patch("enmutils.lib.filesystem.copy")
    @patch("os.listdir")
    @patch("os.path.isdir")
    @patch("enmutils.lib.log.logger.error")
    def test_persistence_restore_with_no_backup_available(self, mock_log_error, mock_isdir, mock_listdir, *_):
        sys.argv = ["persistence", "restore"]
        mock_isdir.return_value = True
        mock_listdir.return_value = []
        persistence.cli()
        self.assertTrue(mock_log_error.called)

    @patch("enmutils.lib.init.exit")
    @patch("enmutils.lib.persistence.default_db")
    @patch("enmutils.lib.persistence.Persistence.shutdown")
    @patch("enmutils.lib.init.global_init")
    @patch("enmutils.lib.filesystem.copy")
    @patch("os.listdir")
    @patch("os.path.isdir")
    @patch("enmutils.lib.log.logger.info")
    def test_persistence_restore_success(self, mock_log_info, mock_isdir, mock_listdir, *_):
        mock_isdir.return_value = True
        mock_listdir.return_value = ["path/to/backup/file.db"]
        sys.argv = ["persistence", "restore"]
        persistence.cli()
        self.assertTrue(mock_log_info.call_count == 2)

    @patch('enmutilsbin.persistence.log.yellow_text')
    def test_get__logs_missing_key(self, mock_yellow):
        db = Mock()
        db.has_key.return_value = False
        persistence.get("key", db, False)
        mock_yellow.assert_called_with("Key key was not found in the persistence store")

    @patch('enmutilsbin.persistence.log.logger.info')
    @patch('enmutilsbin.persistence.log.yellow_text')
    def test_get__detailed_key_not_an_object(self, mock_yellow, mock_info):
        db = Mock()
        db.has_key.return_value = True
        db.get.return_value = "0"
        persistence.get("key", db, True)
        self.assertEqual(0, mock_yellow.call_count)
        mock_info.assert_called_with("key = 0")

    @patch('enmutilsbin.persistence.pprint')
    @patch('enmutilsbin.persistence.log.yellow_text')
    def test_get__detailed(self, mock_yellow, mock_pprint):
        db = Mock()
        db.has_key.return_value = True
        db.get.return_value = Mock()
        persistence.get("key", db, True)
        self.assertEqual(0, mock_yellow.call_count)
        self.assertEqual(1, mock_pprint.pformat.call_count)

    @patch('enmutilsbin.persistence.log.logger.info')
    @patch('enmutilsbin.persistence.log.yellow_text')
    def test_get__returns_false_values_not_none(self, mock_yellow, mock_info):
        db = Mock()
        db.has_key.return_value = True
        db.get.return_value = 0
        persistence.get("key", db, True)
        self.assertEqual(0, mock_yellow.call_count)
        mock_info.assert_called_with("key = 0")
        db.get.return_value = []
        persistence.get("key", db, True)
        mock_info.assert_called_with("key = []")

    @patch('enmutilsbin.persistence.log_in_json_format')
    def test_get__calls_log_in_json_format_for_json_argument(self, mock_log_in_json):
        db = Mock()
        db.has_key.return_value = True
        db.get.return_value = 0
        persistence.get("key", db, False, True)
        self.assertEqual(1, mock_log_in_json.call_count)

    @patch('enmutilsbin.persistence.log.logger.info')
    def test_log_in_json_format__logs_dict_data_as_expected(self, mock_info):
        mock_value = Mock()
        mock_value.__dict__ = {"FM_01": [datetime(2020, 12, 12), object()]}
        persistence.log_in_json_format(mock_value)
        self.assertRegexpMatches(mock_info.call_args[0][0],
                                 r'{"FM_01": \["2020-12-12 00:00:00", "<object object at (.*)>"\]}')

    @patch('enmutilsbin.persistence.log.logger.info')
    def test_log_in_json_format__logs_non_dict_data_as_expected(self, mock_info):
        persistence.log_in_json_format({"FM_01", "CMSYNC_01", "PM_01"})
        self.assertRegexpMatches(mock_info.call_args[0][0], r'["FM_01", "CMSYNC_01", "PM_01"]')


if __name__ == "__main__":
    unittest2.main(verbosity=2)
