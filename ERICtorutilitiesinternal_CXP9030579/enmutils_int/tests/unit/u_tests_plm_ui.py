#!/usr/bin/env python
import unittest2
from mock import Mock, patch, mock_open
from requests.exceptions import HTTPError
from enmutils_int.lib.plm_ui import import_multipart_file_to_plm
from testslib import unit_test_utils


class PLMUiRestUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.plm_ui.raise_for_status')
    @patch("enmutils.lib.enm_user_2.User.post")
    @patch("enmutils_int.lib.plm_ui.string")
    def test_import_multipart_file_to_plm_is_successful(self, mock_string, *_):
        mock_string.digits.return_value = "0123456789"
        mock_open_file = mock_open(read_data="test")
        response = Mock()
        response.status_code = 200
        self.user.post.return_value = response
        with patch('__builtin__.open', mock_open_file):
            import_multipart_file_to_plm(self.user, "PLMImport1.csv", "/tmp/PLMImport1.csv")
            self.assertTrue(self.user.post.called)

    @patch("time.sleep")
    @patch("enmutils.lib.enm_user_2.User.post")
    @patch('enmutils_int.lib.plm_ui.raise_for_status')
    @patch("enmutils_int.lib.plm_ui.string")
    def test_import_multipart_file_to_plm_raises_http_error(self, mock_string, mock_raise_for_status, *_):
        mock_string.digits.return_value = "0123456789"
        mock_open_file = mock_open(read_data="test")
        response = Mock()
        response.status_code = 501
        self.user.post.return_value = response
        mock_raise_for_status.side_effect = HTTPError
        with patch('__builtin__.open', mock_open_file):
            self.assertRaises(HTTPError, import_multipart_file_to_plm, self.user, "PLMImport.csv", "/tmp/PLMImport.csv")
            self.assertTrue(self.user.post.called)


if __name__ == '__main__':
    unittest2.main(verbosity=2)
