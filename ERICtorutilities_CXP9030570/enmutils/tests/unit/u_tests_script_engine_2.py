#!/usr/bin/env python
from datetime import datetime, timedelta

import unittest2
from mock import Mock, patch, mock_open
from requests.exceptions import HTTPError

from enmutils.lib.exceptions import TimeOutError
from enmutils.lib.script_engine_2 import Request, Response
from testslib import unit_test_utils

URL = "http://localhost"
APACHE_URL = "https://apache"
PROCESS_ID = 'AQIC5wM2LY4SfcxAck9fvJEG1DFIfH30hU7JvYfAnoRO1AU:43e3bf13'
CMD_URL = 'AQIC5wM2LY4SfcxAck9fvJEG1DFIfH30hU7JvYfAnoRO1AU:43e3bf13'
DATE_STR = 'Thu, 21 Jan 2016 14:56:20 GMT'
CONTENT_TYPE = 'text/plain; charset=UTF-8'
ME_COUNT = "cmedit get * MeContext --count"
INSTANCES_FOUND = "11118 instance(s)"
ME_FOUND = "MeContext {0} found".format(INSTANCES_FOUND)


class ScriptEngineUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.request = Request(command='cmedit get * NetworkElement', user=self.user)

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils.lib.script_engine_2.cache.get_apache_url")
    def test_execute_is_successful_if_requests_are_successful(self, mock_apache_url):
        mock_apache_url.return_value = APACHE_URL

        post_response = Mock(status_code=201, text='')
        post_response.headers = {"process_id": PROCESS_ID}
        post_response.json.return_value = {'content-length': '0',
                                           'process_id': PROCESS_ID,
                                           'commandstatus': 'RUNNING',
                                           'location': CMD_URL, 'cache-control': 'no-cache',
                                           'date': DATE_STR,
                                           'content-type': CONTENT_TYPE}

        get_response = Mock(status_code=200)
        get_response.json.return_value = ({"dtoType": "line", "value": "FDN : NetworkElement=netsim_LTE02ERBS00007"},
                                          {"dtoType": "line", "value": "FDN : NetworkElement=netsim_LTE04ERBS00021"},
                                          {"dtoType": "line", "value": "FDN : NetworkElement=netsim_LTE04ERBS00064"},
                                          {"dtoType": "line", "value": "3 instance(s)"},
                                          {"dtoType": "summary", "errorCode": 0})

        self.user.post.return_value = post_response
        self.user.get.return_value = get_response
        self.assertEqual(len(self.request.execute().get_output()), 4)
        self.assertEqual(self.request.req_id, PROCESS_ID)

    @patch("enmutils.lib.script_engine_2.cache.get_apache_url")
    def test_execute_raises_http_error_if_post_fails(self, mock_apache_url):
        mock_apache_url.return_value = APACHE_URL

        post_response = Mock()
        post_response.text = ''
        post_response.status_code = 500

        self.user.post.return_value = post_response
        self.assertRaises(HTTPError, self.request.execute)

    @patch('time.sleep')
    @patch("enmutils.lib.script_engine_2.cache.get_apache_url")
    def test_execute_raises_http_error_if_get_fails(self, mock_apache_url, _):
        mock_apache_url.return_value = APACHE_URL

        post_response = Mock(status_code=201)
        post_response.headers = {'content-length': '0', 'process_id': PROCESS_ID, 'commandstatus': 'RUNNING',
                                 'location': CMD_URL, 'cache-control': 'no-cache', 'date': DATE_STR,
                                 'content-type': CONTENT_TYPE}

        get_response = Mock(status_code=500)

        self.user.post.return_value = post_response
        self.user.get.return_value = get_response

        self.assertRaises(HTTPError, self.request.execute)

    @patch('time.sleep')
    @patch("enmutils.lib.script_engine_2.cache.get_apache_url")
    def test_get_when_complete_returns_a_response_when_summary_dto_found(self, *_):

        response = Mock(status_code=200)
        response.json.return_value = ({"dtoType": "command", "value": ME_COUNT},
                                      {"dtoType": "line", "value": ME_FOUND},
                                      {"dtoType": "line", "value": None}, {"dtoType": "line", "value": ""},
                                      {"dtoType": "line", "value": INSTANCES_FOUND})

        response1 = Mock(status_code=200)
        response1.json.return_value = ({"dtoType": "command", "value": ME_COUNT},
                                       {"dtoType": "line", "value": ME_FOUND},
                                       {"dtoType": "line", "value": None}, {"dtoType": "line", "value": ""},
                                       {"dtoType": "line", "value": INSTANCES_FOUND},
                                       {"dtoType": "summary", "errorCode": 0, "statusMessage": INSTANCES_FOUND,
                                        "errorMessage": None, "suggestedSolution": None,
                                        "logReference": "st:96a088b7-b947-4743-b3a9-b568f29bd2c9(confirmation)"})

        self.user.get.side_effect = [response, response1]

        self.request._timeout_time = datetime.now() + timedelta(seconds=10)
        self.assertIsNotNone(self.request._get_on_completion()[-1])

    @patch('enmutils.lib.script_engine_2.Request._get_on_completion', side_effect=TimeOutError())
    @patch("enmutils.lib.script_engine_2.cache.get_apache_url")
    def test_execute_raises_timeout_error_if_command_times_out_prior_to_completion(self, mock_apache_url, _):
        mock_apache_url.return_value = APACHE_URL

        post_response = Mock(status_code=201, text='')
        post_response.headers = {'content-length': '0',
                                 'process_id': PROCESS_ID,
                                 'commandstatus': 'RUNNING',
                                 'location': CMD_URL,
                                 'cache-control': 'no-cache', 'date': DATE_STR,
                                 'content-type': CONTENT_TYPE}

        response = Mock(status_code=200)
        response.json.return_value = ({"dtoType": "command", "value": ME_COUNT},
                                      {"dtoType": "line", "value": ME_FOUND},
                                      {"dtoType": "line", "value": None}, {"dtoType": "line", "value": ""},
                                      {"dtoType": "line", "value": INSTANCES_FOUND})

        self.user.post.side_effect = [post_response, response]
        self.request.timeout = .001
        self.assertRaises(TimeOutError, self.request.execute)

    @patch('enmutils.lib.script_engine_2.os')
    def test_request_init__file_in_os_error(self, mock_os):
        mock_os.path.isfile.return_value = False
        self.assertRaises(OSError, Request, command='cmd', user=self.user, file_in="file")

    def test_response_json__http_instance_returned(self):
        http_response = Mock()
        http_response.json.return_value = {}
        response = Response(http_response, 'some_cmd')
        self.assertDictEqual(response.json, {})

    @patch('__builtin__.open', new_callable=mock_open)
    def test_request_post__with_file(self, mock_open_file):
        mock_file = Mock(name="File")
        response = Mock(status_code=201, headers={"process_id": "id"})
        self.user.post.return_value = response
        self.request.file_in = mock_file
        self.request._post()
        self.assertEqual(1, mock_open_file.call_count)

    @patch('enmutils.lib.script_engine_2.urljoin', return_value="url")
    @patch('enmutils.lib.script_engine_2.cache.get_apache_url', return_value="url")
    @patch('enmutils.lib.script_engine_2.Request._response_contains_summary_dtotype', return_value=False)
    @patch('enmutils.lib.script_engine_2.time.sleep', return_value=0)
    @patch('enmutils.lib.script_engine_2.datetime')
    def test_request_get__raises_timeout_error(self, mock_datetime, *_):
        response = Mock(status_code=200, headers={"process_id": "id"})
        self.request._timeout_time = 0
        mock_datetime.now.return_value = 1
        self.user.get.return_value = response
        self.assertRaises(TimeOutError, self.request._get_on_completion)

    @patch('enmutils.lib.script_engine_2.urljoin', return_value="url")
    @patch('enmutils.lib.script_engine_2.cache.get_apache_url', return_value="url")
    @patch('enmutils.lib.script_engine_2.Request._response_contains_summary_dtotype', side_effect=[False, True])
    @patch('enmutils.lib.script_engine_2.time.sleep', return_value=0)
    @patch('enmutils.lib.script_engine_2.datetime')
    def test_request_get__no_json(self, mock_datetime, *_):
        response = Mock(status_code=200, headers={"process_id": "id"})
        response.json.return_value = {}
        self.request._timeout_time = 1
        mock_datetime.now.return_value = 0
        self.user.get.return_value = response
        self.request._get_on_completion()
        self.assertEqual(2, self.user.get.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
