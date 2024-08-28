#!/usr/bin/env python
import os
import sys
import tempfile
import unittest2

from enmutils.lib import config
from mock import patch, call, Mock, mock_open

from testslib import unit_test_utils


class ConfigUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_is_a_cloud_deployment__returns_true_if_emp_exists_in_the_global_config_dict(self):
        config.GLOBAL_CONFIG_DICT["EMP"] = "Exists"

        self.assertTrue(config.is_a_cloud_deployment())

    @patch("enmutils.lib.config.os")
    def test_is_a_cloud_deployment__returns_true_if_emp_exists_in_the_os_environment(self, mock_os):
        mock_os.environ = {"EMP": "Exists"}
        self.assertTrue(config.is_a_cloud_deployment())

    @patch("enmutils.lib.config.os")
    def test_is_a_cloud_deployment__returns_false_if_emp_does_not_exist_in_the_os_environment_or_the_global_config_dict(
            self, mock_os):
        mock_os.environ = {}
        self.assertFalse(config.is_a_cloud_deployment())

    def test_write_config_to_file__successful(self):
        test_config_file_path = "/var/tmp/test_file"
        test_config = {"key1": "val1", "key2": "val2", "key3": "val3"}

        config._write_config_to_file(test_config, test_config_file_path)

        expected_lines = ["key1=val1\n", "key2=val2\n", "key3=val3\n"]
        with open(test_config_file_path) as config_file:
            self.assertEqual(sorted(expected_lines), sorted(config_file.readlines()))
        os.remove(test_config_file_path)

    def test_update_config_file_file__does_not_exist_throws_exception(self):
        with self.assertRaises(IOError):
            config.update_config_file("non_existant_file", "key", "value")

    @patch("enmutils.lib.config._parse_conf_line")
    @patch("enmutils.lib.config.shutil.move")
    @patch('__builtin__.open', new_callable=mock_open)
    def test_update_config_file_file__success(self, mock_open_file, mock_shutil_move, mock_parse):
        tempfile_test = tempfile.mkstemp()[1]
        mock_parse.return_value = ["key1"]
        mock_open_file.return_value.readlines.return_value = ["key1=value2", "key2=value2"]
        config.update_config_file(tempfile_test, "key1", ['1', '2', '3', ',', '|||'])
        self.assertTrue(mock_open_file.return_value.write.called)
        self.assertTrue(mock_shutil_move.called)
        os.remove(tempfile_test)

    @patch("enmutils.lib.config._parse_conf_line")
    @patch("enmutils.lib.config.shutil.move")
    @patch('__builtin__.open', new_callable=mock_open)
    def test_update_config_file_file__update_property_false(self, mock_open_file, mock_shutil_move, mock_parse):
        tempfile_test = tempfile.mkstemp()[1]
        mock_parse.return_value = ["test"]
        mock_open_file.return_value.readlines.return_value = ["key1=value2", "key2=value2"]
        config.update_config_file(tempfile_test, "key", ['1', '2', '3', ',', '|||'])
        self.assertTrue(mock_shutil_move.called)
        os.remove(tempfile_test)

    @patch("enmutils.lib.config.shutil.move")
    def test_update_config_file_file__string_success(self, mock_shutil_move):
        tempfile_test = tempfile.mkstemp()[1]
        config.update_config_file(tempfile_test, "key", "test, value")
        self.assertTrue(mock_shutil_move.called)
        os.remove(tempfile_test)

    @patch('enmutils.lib.config.base64.b64decode')
    def test_get_encoded_password_and_decode__is_successful(self, mock_base64):
        username = 'workload_admin'
        password = "pass"
        config.get_encoded_password_and_decode(username, password)
        self.assertEqual(mock_base64.call_count, 1)

    @patch('enmutils.lib.config.base64.b64decode')
    def test_get_encoded_password_and_decode__returns_password(self, mock_base64):
        username = 'admin'
        password = "pass"
        config.get_encoded_password_and_decode(username, password)
        self.assertEqual(mock_base64.call_count, 0)

    @patch("enmutils.lib.config.cache.has_key", return_value=True)
    @patch("enmutils.lib.config.load_bashrc_env_variables")
    def test_load_config__does_nothing_if_key_already_in_cache(self, mock_load_bashrc_env_variables, *_):
        self.assertIsNone(config.load_config())
        self.assertFalse(mock_load_bashrc_env_variables.called)

    @patch("enmutils.lib.config.load_bashrc_env_variables")
    @patch("enmutils.lib.config.cache.has_key", return_value=False)
    @patch("enmutils.lib.config.load_config_from_file")
    @patch("enmutils.lib.config.load_local_config")
    @patch("enmutils.lib.config.cache.set")
    def test_load_config__successful_if_key_not_in_cache_for_production_package(
            self, mock_set, mock_load_local_config, mock_load_config_from_file, *_):
        self.assertIsNone(config.load_config())
        mock_set.assert_called_with("config-loaded", True)
        self.assertTrue(mock_load_local_config.called)
        mock_load_config_from_file.assert_called_with(config.PROD_CONFIG_FILE)

    @patch("enmutils.lib.config.load_bashrc_env_variables")
    @patch("enmutils.lib.config.cache.has_key", return_value=False)
    @patch("enmutils.lib.config.pkgutil.get_loader")
    @patch("enmutils.lib.config.os.path.join")
    @patch("enmutils.lib.config.load_config_from_file")
    @patch("enmutils.lib.config.load_local_config")
    @patch("enmutils.lib.config.cache.set")
    def test_load_config__successful_if_key_not_in_cache_for_internal_package(
            self, mock_set, mock_load_local_config, mock_load_config_from_file, mock_join, mock_get_loader, *_):
        self.assertIsNone(config.load_config(tool_class="int"))
        self.assertTrue(mock_set.called)
        self.assertTrue(mock_load_local_config.called)
        self.assertTrue(call(config.PROD_CONFIG_FILE) in mock_load_config_from_file.mock_calls)
        self.assertTrue(call(mock_join.return_value) in mock_load_config_from_file.mock_calls)
        mock_join.assert_called_with(mock_get_loader.return_value.filename, "etc", "properties.conf")

    @patch("enmutils.lib.config.os")
    @patch("enmutils.lib.config.commands.getstatusoutput", return_value=(0, "some_output\n"))
    def test_load_bashrc_env_variables__successful_if_variable_is_defined_in_bashrc(
            self, mock_getstatusoutput, mock_os):
        mock_os.path.isfile.return_value = True
        mock_os.environ = {}
        config.load_bashrc_env_variables()
        getstatusoutput_calls = [
            call("source /root/.bashrc; echo $LMS_HOST"), call("source /root/.bashrc; echo $EMP"),
            call("source /root/.bashrc; echo $ENM_URL"), call("source /root/.bashrc; echo $DEPLOYMENTNAME")]
        self.assertEqual(getstatusoutput_calls, mock_getstatusoutput.mock_calls)
        self.assertEqual(mock_os.environ["LMS_HOST"], "some_output")
        self.assertEqual(mock_os.environ["EMP"], "some_output")
        self.assertEqual(mock_os.environ["ENM_URL"], "some_output")
        self.assertEqual(mock_os.environ["DEPLOYMENTNAME"], "some_output")

    @patch("enmutils.lib.config.os")
    @patch("enmutils.lib.config.commands.getstatusoutput", return_value=(1, ""))
    def test_load_bashrc_env_variables__does_not_update_environ_if_variable_not_defined_in_bashrc(
            self, mock_getstatusoutput, mock_os):
        mock_os.path.isfile.return_value = True
        mock_os.environ = {}
        config.load_bashrc_env_variables()
        self.assertEqual(mock_getstatusoutput.call_count, 4)
        self.assertEqual(mock_os.environ, {})

    @patch("enmutils.lib.config.os")
    @patch("enmutils.lib.config.commands.getstatusoutput", return_value=(1, ""))
    def test_load_bashrc_env_variables__does_nothing_if_bashrc_does_not_exist(
            self, mock_getstatusoutput, mock_os):
        mock_os.path.isfile.return_value = False
        mock_os.environ = {}
        config.load_bashrc_env_variables()
        self.assertFalse(mock_getstatusoutput.called)
        self.assertEqual(mock_os.environ, {})

    @patch('enmutils.lib.config.pkgutil.get_loader', return_value=Mock())
    @patch('enmutils.lib.config.os.path.join', return_value="")
    @patch('enmutils.lib.config.filesystem.does_file_exist', return_value=True)
    @patch('enmutils.lib.config.parse_conf_file', return_value={'username': 'username', 'password': 'password'})
    def test_load_credentials_from_props__success(self, *_):
        user, passwd = config.load_credentials_from_props()
        self.assertEqual(user, 'username')
        self.assertEqual(passwd, 'password')

    @patch('enmutils.lib.config.pkgutil.get_loader', return_value=Mock())
    @patch('enmutils.lib.config.os.path.join', return_value="")
    @patch('enmutils.lib.config.filesystem.does_file_exist', return_value=True)
    @patch('enmutils.lib.config.parse_conf_file', return_value={'username1': 'username1', 'password': 'password'})
    def test_load_credentials_from_props__username_not_found(self, *_):
        creds = config.load_credentials_from_props()
        self.assertEqual(creds, ())

    @patch('enmutils.lib.config.pkgutil.get_loader', return_value=Mock())
    @patch('enmutils.lib.config.os.path.join', return_value="")
    @patch('enmutils.lib.config.filesystem.does_file_exist', return_value=False)
    @patch('enmutils.lib.config.parse_conf_file')
    def test_load_credentials_from_props__file_not_found(self, mock_parse, *_):
        creds = config.load_credentials_from_props()
        self.assertEqual(creds, ())
        self.assertEqual(0, mock_parse.call_count)

    @patch('enmutils.lib.config.pkgutil.get_loader', return_value=None)
    @patch('enmutils.lib.config.os.path.join')
    def test_load_credentials_from_props__no_internal_package(self, mock_join, _):
        creds = config.load_credentials_from_props()
        self.assertEqual(creds, ())
        self.assertEqual(0, mock_join.call_count)

    def test_load_local_config__import_error_exception(self):
        save_attr = getattr(sys.modules['enmutils'], 'local_properties')
        delattr(sys.modules['enmutils'], 'local_properties')
        self.assertEqual(config.load_local_config(), None)
        setattr(sys.modules['enmutils'], 'local_properties', save_attr)

    def test_get_prop__raise_runtime_error(self):
        config.GLOBAL_CONFIG_DICT = {}
        with self.assertRaises(RuntimeError):
            config.get_prop("user1")

    def test_set_prop__raise_runtime_error_for_None(self):
        with self.assertRaises(RuntimeError):
            config.set_prop("user", None)

    @patch("enmutils.lib.config.load_config")
    def test_set_prop__if_global_config_dict_is_empty(self, mock_load_config):
        temp = config.GLOBAL_CONFIG_DICT
        config.GLOBAL_CONFIG_DICT = {}
        config.set_prop("test_key", "test_value")
        self.assertTrue(mock_load_config.called)
        config.GLOBAL_CONFIG_DICT = temp

    @patch("enmutils.lib.config.load_config")
    def test_set_prop__if_value_is_not_None_and_global_config_is_not_empty(self, mock_load_config):
        config.set_prop("user", "admin")
        self.assertFalse(mock_load_config.called)

    @patch("enmutils.lib.config.load_config")
    def test_set_prop__if_value_is_list(self, mock_load_config):
        config.set_prop("user", ["admin"])
        self.assertFalse(mock_load_config.called)

    @patch("enmutils.lib.config.has_prop", return_value=True)
    @patch("enmutils.lib.config.get_prop")
    def test_get_nodes_data_dir__has_prop_success(self, mock_get_prop, mock_has_prop):
        self.assertTrue(config.get_nodes_data_dir(), mock_get_prop)

    @patch("enmutils.lib.config.has_prop", return_value=False)
    @patch("enmutils.lib.config.get_prop")
    def test_get_nodes_data_dir__success(self, mock_get_prop, mock_has_prop):
        self.assertTrue(config.get_nodes_data_dir(), mock_get_prop)

    @patch("enmutils.lib.config.get_environ")
    @patch("enmutils.lib.config.has_prop", return_value=True)
    @patch("enmutils.lib.config.get_prop")
    def test_get_log_dir__has_prop_success(self, mock_get_prop, mock_has_prop, mock_get_environ):
        mock_get_environ.return_value = 'test'
        self.assertTrue(config.get_log_dir(), mock_get_prop)

    @patch("enmutils.lib.config.os")
    def test_get_log_dir__present_in_os_enivron(self, mock_os):
        output = {'ENMUTILS_LOG_DIR': "test_log_directory"}
        mock_os.environ = output
        self.assertEqual(config.get_log_dir(), "test_log_directory")

    @patch("enmutils.lib.config.get_environ")
    @patch("enmutils.lib.config.has_prop", return_value=False)
    @patch("enmutils.lib.config.get_prop")
    def test_get_log_dir__success(self, mock_get_prop, mock_has_prop, mock_get_environ):
        mock_get_environ.return_value = 'production'
        self.assertTrue(config.get_log_dir(), mock_get_prop)

    @patch("enmutils.lib.config.get_prop")
    @patch("enmutils.lib.config.has_prop", side_effect=[True, False])
    @patch("enmutils.lib.config.get_environ")
    def test_get_redis_db_index__returns_from_get_prop(self, mock_get_environ, mock_has_prop, mock_get_prop):
        mock_get_environ.return_value = 'test'
        self.assertTrue(config.get_redis_db_index(), mock_get_prop)
        self.assertFalse(config.get_redis_db_index(), 0)

    @patch("enmutils.lib.config.os")
    @patch("enmutils.lib.config.get_environ")
    def test_get_redis_db_index__returns_from_os_environ(self, mock_get_environ, mock_os):
        mock_get_environ.return_value = 'test'
        output = {'REDIS_DB_INDEX': "5"}
        mock_os.environ = output
        self.assertEqual(config.get_redis_db_index(), 5)

    def test__parse_conf_line__if_equal_not_there_in_line(self):
        test_return_value = config._parse_conf_line("test_line")
        self.assertEqual(test_return_value, (None, None))

    def test__parse_conf_line__if_or_symbol_present_in_property_value(self):
        test_return_value = config._parse_conf_line("test=line||| =message")
        self.assertEqual(test_return_value, ('test', ['line', '=message']))

    @patch("enmutils.lib.config.load_config")
    def test_get_config_dict__success(self, mock_load_config):
        temp = config.GLOBAL_CONFIG_DICT
        config.GLOBAL_CONFIG_DICT = {}
        config.get_config_dict()
        self.assertTrue(mock_load_config.called)
        config.GLOBAL_CONFIG_DICT = temp

if __name__ == "__main__":
    unittest2.main(verbosity=2)
