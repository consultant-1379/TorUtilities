#!/usr/bin/env python
import unittest2
from mock import patch, Mock

from enmutils_int.lib.alex_doc import get_doc_url, URLS_TO_VISIT
from testslib import unit_test_utils


class AlexDocUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.request_key = ('GET', 'http://test.com/elex')
        self.user = Mock(ui_response_info={self.request_key: {True: 0, False: 0}})
        self.doc_error_msg = "<title>ELEX Error Message</title>"

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.alex_doc.log.logger.debug')
    def test_get_doc_url__catches_doc_error(self, mock_debug):
        response = Mock(ok=True, text=self.doc_error_msg)
        self.user.get.return_value = response
        get_doc_url(self.user, '/elex')
        mock_debug.assert_called_with('FAILED URL: /elex')

    def test_get_doc_url__catches_doc_error_increments_correct_request(self):
        response = Mock(ok=True, text=self.doc_error_msg)
        self.user.get.return_value = response
        get_doc_url(self.user, URLS_TO_VISIT[0])
        self.assertEqual(self.user.ui_response_info.get(self.request_key).get(False), 0)

    def test_get_doc_url__is_successful(self):
        response = Mock(ok=True, text="Some helpful content")
        self.user.get.return_value = response
        get_doc_url(self.user, '/elex')
        self.assertEqual(self.user.ui_response_info.get(self.request_key).get(False), 0)

    @patch('enmutils_int.lib.alex_doc.log.logger.debug')
    def test_get_doc_url__returns_altered_response_if_lib_not_found(self, _):
        url = 'http://test.com/elex'
        response = Mock(ok=True, text=self.doc_error_msg, request=Mock(method="GET", url=url))
        self.user.get.return_value = response
        get_doc_url(self.user, url)

        self.assertEqual(self.user.ui_response_info.get(self.request_key).get(False), 1)
        self.assertEqual(self.user.ui_response_info.get(self.request_key).get(True), -1)
        self.assertEqual(response._content,
                         'ENMUtils response - URL: http://test.com/elex not found in the ELEX library')
        self.assertEqual(response.status_code, 599)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
