import unittest2
from mock import patch, Mock

from enmutils.lib import http
from enmutils.lib.http import Response, Request
from testslib import unit_test_utils


class ResponseUnitTests(unittest2.TestCase):
    def setUp(self):
        unit_test_utils.setup()
        self._response = Mock()
        self.id = Mock()
        self.job = Response(requests_response=self._response)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils.lib.http.timestamp")
    def test_log(self, _):
        mock_request = Mock()
        mock_request.text = "Test Text"
        mock_request.status_code = 400
        test_obj = Response(mock_request)
        self.assertEqual(test_obj.log(), None)

    @patch("enmutils.lib.http.timestamp")
    def test_log__all_conditions(self, _):
        mock_request = Mock()
        mock_request.text = None
        mock_request.headers = None
        mock_request.status_code = 200
        mock_request.reason = None
        test_obj = Response(mock_request)
        self.assertEqual(test_obj.log(), None)

    def test_output_success(self):
        mock_request = Mock()
        mock_request.text = "test text"
        test_obj = Response(mock_request)
        self.assertEqual(test_obj.output, "test text")

    def test_rc_success(self):
        mock_request = Mock()
        mock_request.status_code = 200
        test_obj = Response(mock_request)
        self.assertEqual(test_obj.rc, 200)

    def test_headers_success(self):
        mock_request = Mock()
        mock_request.headers = "test headers"
        test_obj = Response(mock_request)
        self.assertEqual(test_obj.headers, "test headers")

    def test_json_success(self):
        mock_request = Mock()
        mock_request.json = "test json"
        test_obj = Response(mock_request)
        self.assertEqual(test_obj.json, "test json")

    @patch("enmutils.lib.http.Request.execute")
    def test_get_success(self, mock_execute):
        http.get("get url")
        self.assertTrue(mock_execute.called)

    @patch("enmutils.lib.http.Request.execute")
    def test_post_success(self, mock_execute):
        http.post("post url")
        self.assertTrue(mock_execute.called)

    @patch("enmutils.lib.http.Request.execute")
    def test_put_success(self, mock_execute):
        http.put("put url")
        self.assertTrue(mock_execute.called)

    @patch("enmutils.lib.http.Request.execute")
    def test_delete_success(self, mock_execute):
        http.delete("delete url")
        self.assertTrue(mock_execute.called)


class RequestUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.method = Mock()
        self.url = Mock()
        self.job = Request(method=self.method, url=self.url)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_log_response_success(self):
        mock_response = Mock()
        mock_response.data = "test data"
        mock_response.headers = "test headers"
        mock_response.json = "test json"
        mock_response.params = "test params"
        test_obj = Request(mock_response, Mock())
        self.assertEqual(test_obj.log(), None)

    def test_log_response_all_conditions_success(self):
        mock_response = Mock()
        test_obj = Request(mock_response, Mock(), data="test", headers="test_h", json="test json", params="test params")
        self.assertEqual(test_obj.log(), None)

    @patch("enmutils.lib.http.requests")
    @patch("enmutils.lib.http.Response")
    def test_execute(self, mock_response, _):
        mock_request = Mock()
        mock_request.url = "test url"
        mock_request.id = 5
        mock_response.return_value = mock_request
        test_obj = Request(mock_response, "mock_response")
        test_obj.execute()

    @patch("enmutils.lib.http.requests")
    @patch("enmutils.lib.http.Response")
    def test_execute_verbose(self, mock_response, _):
        mock_request = Mock()
        mock_request.url = "test url"
        mock_request.id = 5
        mock_response.return_value = mock_request
        test_obj = Request(mock_response, "mock_response", verbose=False)
        test_obj.execute()

    def test_getattr_success(self):
        mock_resp = Mock()
        mock_resp.text = "text"
        obj = Response(mock_resp)
        self.assertEqual(getattr(obj, "text"), "text")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
