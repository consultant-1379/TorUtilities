#!/usr/bin/env python
import unittest2
from mock import Mock, patch

from enmutils_int.lib.simple_sftp_client import (get_proxy_details, open_sftp_session, download, sftp_get, upload,
                                                 sftp_put, download_file)
from testslib import unit_test_utils

HOST = "host"
USER = "user"
PASS = "passwd"
REMOTE_FILE_PATH = "/some/path"


class SimpleSFTPClientUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.simple_sftp_client.cache.is_emp', return_value=False)
    @patch('enmutils_int.lib.simple_sftp_client.cache.get_ms_host', return_value=HOST)
    def test_get_proxy_details__physical(self, *_):
        self.assertEqual(("root", HOST, None), get_proxy_details())

    @patch('enmutils_int.lib.simple_sftp_client.cache.is_emp', return_value=True)
    @patch('enmutils_int.lib.simple_sftp_client.cache.get_emp', return_value=HOST)
    def test_get_proxy_details__cloud(self, *_):
        self.assertEqual(("cloud-user", HOST, "/var/tmp/enm_keypair.pem"), get_proxy_details())

    @patch('enmutils_int.lib.simple_sftp_client.paramiko.SFTPClient.from_transport')
    @patch('enmutils_int.lib.simple_sftp_client.log.logger.debug')
    @patch('enmutils_int.lib.simple_sftp_client.paramiko.Transport')
    def test_open_sftp_session__success(self, mock_transport, mock_debug, _):
        open_sftp_session(HOST, USER, PASS)
        self.assertEqual(1, mock_transport.return_value.connect.call_count)
        mock_debug.assert_called_with("Successfully opened SFTPClient for host: [{0}].".format(HOST))

    @patch('enmutils_int.lib.simple_sftp_client.paramiko.SFTPClient.from_transport')
    @patch('enmutils_int.lib.simple_sftp_client.cache.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.simple_sftp_client.get_proxy_details', return_value=(USER, HOST, None))
    @patch('enmutils_int.lib.simple_sftp_client.create_proxy')
    @patch('enmutils_int.lib.simple_sftp_client.paramiko.Transport')
    def test_open_sftp_session__creates_proxy(self, mock_transport, mock_create_proxy, *_):
        open_sftp_session(HOST, USER, PASS, use_proxy=True)
        self.assertEqual(1, mock_transport.return_value.connect.call_count)
        self.assertEqual(1, mock_create_proxy.call_count)

    @patch('enmutils_int.lib.simple_sftp_client.close_proxy')
    def test_sftp_get__success(self, close_proxy):
        client = Mock()
        sftp_get(client, REMOTE_FILE_PATH, REMOTE_FILE_PATH)
        self.assertEqual(0, close_proxy.call_count)
        self.assertEqual(1, client.get.call_count)
        self.assertEqual(1, client.close.call_count)

    @patch('enmutils_int.lib.simple_sftp_client.close_proxy')
    def test_sftp_get__closes_proxy_object(self, close_proxy):
        client, proxy = Mock(), Mock()
        sftp_get(client, REMOTE_FILE_PATH, REMOTE_FILE_PATH, proxy=proxy)
        self.assertEqual(1, close_proxy.call_count)
        self.assertEqual(1, client.get.call_count)
        self.assertEqual(1, client.close.call_count)

    @patch('enmutils_int.lib.simple_sftp_client.open_sftp_session', return_value=(Mock(), None))
    @patch('enmutils_int.lib.simple_sftp_client.sftp_get')
    def test_download__opens_client_gets_file(self, mock_get, mock_open):
        download(HOST, USER, PASS, REMOTE_FILE_PATH, REMOTE_FILE_PATH)
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(1, mock_open.call_count)

    def test_sftp_put__success(self):
        client, proxy = Mock(), Mock()
        sftp_put(client, REMOTE_FILE_PATH, REMOTE_FILE_PATH, proxy=proxy)
        self.assertEqual(1, client.chdir.call_count)
        self.assertEqual(1, client.put.call_count)
        self.assertEqual(1, client.close.call_count)
        self.assertEqual(1, proxy.close.call_count)

    def test_sftp_put__changes_file_permissions(self):
        client = Mock()
        sftp_put(client, REMOTE_FILE_PATH, REMOTE_FILE_PATH, file_permissions=755)
        self.assertEqual(1, client.chdir.call_count)
        self.assertEqual(1, client.put.call_count)
        self.assertEqual(1, client.close.call_count)
        self.assertEqual(1, client.chmod.call_count)

    def test_sftp_put__creates_directory(self):
        client = Mock()
        client.chdir.side_effect = IOError("Error")
        sftp_put(client, REMOTE_FILE_PATH, REMOTE_FILE_PATH)
        self.assertEqual(1, client.mkdir.call_count)
        self.assertEqual(1, client.put.call_count)
        self.assertEqual(1, client.close.call_count)

    @patch('enmutils_int.lib.simple_sftp_client.open_sftp_session', return_value=(Mock(), None))
    @patch('enmutils_int.lib.simple_sftp_client.sftp_put')
    def test_upload__opens_client_puts_file(self, mock_put, mock_open):
        upload(HOST, USER, PASS, REMOTE_FILE_PATH, REMOTE_FILE_PATH)
        self.assertEqual(1, mock_put.call_count)
        self.assertEqual(1, mock_open.call_count)

    @patch('enmutils_int.lib.simple_sftp_client.shell.connection_mgr')
    @patch('enmutils_int.lib.simple_sftp_client.shell.get_connection_mgr')
    def test_download_file__success(self, mock_get_connection, mock_return):
        connection = Mock()
        mock_get_connection.return_value.get_connection.return_value = connection
        download_file("", "", "", "", "")
        self.assertEqual(1, connection.sftp_client.get.call_count)
        self.assertEqual(1, mock_return.return_connection.call_count)

    @patch('enmutils_int.lib.simple_sftp_client.shell.connection_mgr')
    @patch('enmutils_int.lib.simple_sftp_client.shell.get_connection_mgr')
    def test_download_file__opens_sftp_client(self, mock_get_connection, mock_return):
        connection = Mock()
        delattr(connection, "sftp_client")
        mock_get_connection.return_value.get_connection.return_value = connection
        download_file("", "", "", "", "")
        self.assertEqual(1, connection.open_sftp.call_count)
        self.assertEqual(1, connection.sftp_client.get.call_count)
        self.assertEqual(1, mock_return.return_connection.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
