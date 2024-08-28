#!/usr/bin/env python
import unittest2

from mock import patch, Mock
from enmutils_int.lib.esm import (esm_login, esm_logout, LOGOUT_URL, random_get_request_cn)

from testslib import unit_test_utils

ESM_HOME = "https://ieatenmpd111-7.athtem.eei.ericsson.se:7443"


class ESMUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.username = "User_u0"

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.esm.log.logger.debug")
    def test_esm_login__is_successful(self, mock_log):
        response = Mock()
        self.user.post.return_value = response
        response.status_code = 200
        esm_login(self.username, self.user, ESM_HOME)
        self.assertEqual(mock_log.call_count, 2)
        self.assertFalse(response.raise_for_status.called)

    @patch("enmutils_int.lib.esm.log.logger.debug")
    def test_esm_login__raises_error(self, mock_log):
        response = Mock()
        self.user.post.return_value = response
        response.status_code = 201
        esm_login(self.username, self.user, ESM_HOME)
        self.assertEqual(mock_log.call_count, 1)
        self.assertTrue(response.raise_for_status.called)

    @patch("enmutils_int.lib.esm.log.logger.debug")
    def test_esm_logout__is_successful(self, mock_log):
        response = Mock()
        response.status_code = 200
        self.user.get.return_value = response
        esm_logout(self.username, self.user, ESM_HOME)
        self.user.get.assert_called_with(ESM_HOME + LOGOUT_URL)
        self.assertEqual(mock_log.call_count, 2)
        self.assertFalse(response.raise_for_status.called)

    @patch("enmutils_int.lib.esm.log.logger.debug")
    def test_esm_logout__raises_error(self, mock_log):
        response = Mock()
        self.user.get.return_value = response
        response.status_code = 402
        esm_logout(self.username, self.user, ESM_HOME)
        self.user.get.assert_called_with(ESM_HOME + LOGOUT_URL)
        self.assertEqual(mock_log.call_count, 1)
        self.assertTrue(response.raise_for_status.called)

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.get_esmon_vm_ip')
    @patch("enmutils_int.lib.esm.is_enm_on_cloud_native", return_value=True)
    @patch("enmutils_int.lib.esm.log.logger.debug")
    def test_random_get_request_cn__is_successful(self, mock_log, *_):
        response = Mock()
        self.user.get.return_value = response
        response.status_code = 200
        random_get_request_cn(self.username, self.user, "ip")
        self.assertEqual(mock_log.call_count, 2)
        self.assertFalse(response.raise_for_status.called)

    @patch('enmutils_int.lib.profile_flows.esm_flows.esm_flow.ESM01Flow.get_esmon_vm_ip')
    @patch("enmutils_int.lib.esm.is_enm_on_cloud_native", return_value=False)
    @patch("enmutils_int.lib.esm.log.logger.debug")
    def test_random_get_request_cn__physical_and_cloud(self, mock_log, *_):
        response = Mock()
        self.user.get.return_value = response
        response.status_code = 204
        random_get_request_cn(self.username, self.user, "ip")
        self.assertEqual(mock_log.call_count, 1)
        self.assertTrue(response.raise_for_status.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
