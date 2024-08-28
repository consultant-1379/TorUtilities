#!/usr/bin/env python

import unittest2
from mock import patch, mock_open
from testslib import unit_test_utils
from enmutils_int.external_sources.rpm_post_install.rpm_post_install_script import cli


class RpmPostInstall(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.external_sources.rpm_post_install.rpm_post_install_script.os')
    @patch('enmutils_int.external_sources.rpm_post_install.rpm_post_install_script.pkgutil')
    @patch('enmutils_int.external_sources.rpm_post_install.rpm_post_install_script.log')
    @patch('enmutils_int.external_sources.rpm_post_install.rpm_post_install_script.filesystem')
    def test_add_timeout_to_authenticator_file_updates_file(self, mock_filesystem, mock_log, *_):
        mock_filesystem.does_file_exist.return_value = True
        data = ("logger.debug('Authenticating user [%s]', self._username)\n"
                "        auth_response = session.post(''.join((session.url(), '/login')),\n"
                "                                     data={'IDToken1': self._username, 'IDToken2': self._password},\n"
                "                                     allow_redirects=False)")
        mock_open_file = mock_open(read_data=data)
        with patch('__builtin__.open', mock_open_file) as mock_file:
            mock_file.return_value.__iter__.return_value = data.splitlines()
            cli()
            self.assertEqual(mock_log.logger.info.call_count, 2)

    @patch('enmutils_int.external_sources.rpm_post_install.rpm_post_install_script.os')
    @patch('enmutils_int.external_sources.rpm_post_install.rpm_post_install_script.pkgutil')
    @patch('enmutils_int.external_sources.rpm_post_install.rpm_post_install_script.log')
    @patch('enmutils_int.external_sources.rpm_post_install.rpm_post_install_script.filesystem')
    def test_add_timeout_to_authenticator_file_does_not_update_file_if_timeout_already_present(self, mock_filesystem,
                                                                                               mock_log, *_):
        mock_filesystem.does_file_exist.return_value = True
        data = ("logger.debug('Authenticating user [%s]', self._username)\n"
                "        auth_response = session.post(''.join((session.url(), '/login')), timeout=300,\n"
                "                                     data={'IDToken1': self._username, 'IDToken2': self._password},\n"
                "                                     allow_redirects=False)")
        mock_open_file = mock_open(read_data=data)
        with patch('__builtin__.open', mock_open_file) as mock_file:
            mock_file.return_value.__iter__.return_value = data.splitlines()
            cli()
            self.assertEqual(mock_log.logger.info.call_count, 1)

    @patch('enmutils_int.external_sources.rpm_post_install.rpm_post_install_script.os')
    @patch('enmutils_int.external_sources.rpm_post_install.rpm_post_install_script.pkgutil')
    @patch('enmutils_int.external_sources.rpm_post_install.rpm_post_install_script.log')
    @patch('enmutils_int.external_sources.rpm_post_install.rpm_post_install_script.filesystem')
    def test_add_timeout_to_authenticator_file_does_not_update_if_file_not_present(self, mock_filesystem, mock_log, *_):
        mock_filesystem.does_file_exist.return_value = False
        cli()
        self.assertEqual(mock_log.logger.info.call_count, 0)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
