#!/usr/bin/env python
import unittest2
from mock import Mock
from requests.exceptions import HTTPError

from enmutils.lib.exceptions import InvalidSearchError
from enmutils_int.lib.log_viewer import LogViewer
from testslib import unit_test_utils


class LogViewerUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock(username="TestUser", password="T3stP4ssw0rd")
        search_term = "all errors"
        self.log_viewer = LogViewer(search_term=search_term, user=self.user)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_get_log_viewer_app_raises_invalid_search_error(self):
        response = Mock(status_code=404, text="Not Found")
        response.raise_for_status.side_effect = HTTPError("error")
        self.user.get.return_value = response
        self.assertRaises(HTTPError, self.log_viewer.get_log_viewer)

    def test_get_log_viewer_valid_app_search(self):
        response = Mock(status_code=200, text="")
        self.user.get.return_value = response
        self.assertEqual(self.log_viewer.get_log_viewer(), 200)

    def test_get_log_viewer_app_help_raises_http_error(self):
        response = Mock(status_code=404, text="Not Found")
        response.raise_for_status.side_effect = HTTPError("error")
        self.user.get.return_value = response
        self.assertRaises(HTTPError, self.log_viewer.get_log_viewer_help)

    def test_get_log_viewer_app_help_page(self):
        response = Mock(status_code=200, text="")
        self.user.get.return_value = response
        self.assertEqual(self.log_viewer.get_log_viewer_help(), 200)

    def test_get_log_viewer_app_search_raises_invalid_search_error(self):
        self.log_viewer.search_term = None
        self.assertRaises(InvalidSearchError, self.log_viewer.get_log_viewer_by_search_term)

    def test_get_log_viewer_by_search_term_raises_http_error(self):
        response = Mock(status_code=404, text="Not Found")
        response.raise_for_status.side_effect = HTTPError("error")
        self.user.get.return_value = response
        self.assertRaises(HTTPError, self.log_viewer.get_log_viewer_by_search_term)

    def test_get_log_viewer_by_search_term_is_success(self):
        response = Mock(status_code=200, text='"success"')
        self.user.get.return_value = response
        self.assertEqual(u"success", self.log_viewer.get_log_viewer_by_search_term())


if __name__ == "__main__":
    unittest2.main(verbosity=2)
