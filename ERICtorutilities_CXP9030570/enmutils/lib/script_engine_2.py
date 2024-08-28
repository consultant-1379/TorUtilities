# ********************************************************************
# Name    : Script Engine 2
# Summary : Provides functionality for executing cmserv
#           commands directly on the scripting cluster.
# ********************************************************************

import os
import time
from urlparse import urljoin
from datetime import datetime, timedelta
from requests.exceptions import HTTPError

from enmutils.lib import log, cache
from enmutils.lib.enm_user_2 import get_admin_user
from enmutils.lib.exceptions import TimeOutError


class Request(object):

    POST_ENDPOINT = '/script-engine/services/command'
    GET_ENDPOINT = '/script-engine/services/command/output/{process_id}'
    FILES_ENDPOINT = '/script-engine/services/files'

    def __init__(self, command, file_in=None, user=None, timeout=600):
        """
        ScriptEngineCommand Constructor.

        :param command: command to be executed
        :type command: str
        :param file_in: path of file to be uploaded
        :type file_in: str
        :param user: user to be used to make the REST requests
        :type user: `enm_user.User` object
        :param timeout: timeout to be used when polling for result (in seconds)
        :type timeout: int
        :raises OSError: raises if file is none and file is not in path
        """
        self.user = user or get_admin_user()
        self.command = command
        self.timeout = timeout
        self.file_in = file_in
        self._timeout_time = None

        # Request id returned by making the post request
        self.req_id = None

        if self.file_in and not os.path.isfile(self.file_in):
            raise OSError('File "%s" does not exist' % self.file_in)

    def execute(self):
        """
        Executes the command in the flow (post, poll and get)

        :return: `Response` object
        :rtype: object
        """
        self._post()
        self._timeout_time = datetime.now() + timedelta(seconds=self.timeout)
        return Response(self._get_on_completion(), self.command)

    def _post(self):
        """
        Makes the post request given the command. Stores the req_id from the response

        :raises HTTPError: raises if status code is not 201
        :return: `Response` object
        :rtype: object
        """
        headers = {'X-Requested-With': 'XMLHttpRequest',
                   'Accept': 'text/plain, */*; q=0.01',
                   'Skip-Cache': 'True',
                   'streaming': 'true',
                   'tabId': 'do_not_use'}

        if self.file_in:
            log.logger.debug(
                'Attaching file "%s" to script engine command' % self.file_in)
            file = open(self.file_in, 'rb')  # pylint: disable=redefined-builtin
            data = {'command': self.command, 'fileName': file.name}
            files = {'file:': (file.name, file)}
        else:
            log.logger.debug('POST command does not contain file')
            files = {'name': 'command', 'command': self.command}
            data = None
            log.logger.debug(
                "Executing script-engine post command '{0}'".format(self.command))

        # Make the request
        response = self.user.post(self.POST_ENDPOINT, headers=headers, data=data, files=files)
        if response.status_code != 201:
            log.logger.debug("ERROR: Script-engine POST request with command payload"
                             " '{0}' produced http status code {1}".format(self.command, response.status_code))
            raise HTTPError(
                'Failed to make the post request while executing cmd "%s"' % self.command, response=response)
        self.req_id = response.headers["process_id"]

        return response

    def _get_on_completion(self):
        """
        Makes multiple get request and returns the response when it contains a summary dtoType

        :return: `Response` object
        :rtype: object
        :raises TimeOutError: raises if there is timeout
        :raises HTTPError: raises if response code is not 200
        """

        headers = {'Accept': 'application/json',
                   'Connection': 'keep - alive', 'wait_interval': 200,
                   'X-Requested-With': 'XMLHttpRequest'}
        log.logger.debug(
            "Fetching command response from {0} for id {1}".format(urljoin(cache.get_apache_url(), self.GET_ENDPOINT),
                                                                   self.req_id))
        responses = []
        response = self.user.get(self.GET_ENDPOINT.format(process_id=self.req_id), headers=headers)

        # Check if the request was successful
        if response.status_code != 200:
            raise HTTPError(
                'Failed to make the get request while executing cmd "%s"' % self.command, response=response)

        if not self._response_contains_summary_dtotype(response):
            time.sleep(.5)
            if datetime.now() > self._timeout_time:
                log.logger.debug("TIMEOUT! Last Response: {}".format(response.json()))
                raise TimeOutError("Command '{0}' state did not complete before timeout expired "
                                   "[{1}s].".format(self.command, self.timeout))

            if response.json():
                responses.append(response)
            responses.extend(self._get_on_completion())
            return responses
        else:
            log.logger.debug(
                "PASS: Script-engine command response GET request executed successfully")
            return [response]

    @staticmethod
    def _response_contains_summary_dtotype(response):
        return 'summary' in [line['dtoType'] for line in response.json() if 'dtoType' in line and line['dtoType']]


class Response(object):
    def __init__(self, responses, command):
        """
        Response to be used for script engine

        :param responses: list of http response
        :type responses: List of `requests.models.Response`
        :param command: command to be executed
        :type command: str
        """
        self.http_responses = responses
        self.command = command

    @property
    def json(self):
        json_values = []
        if isinstance(self.http_responses, list):
            for response in self.http_responses:
                json_values.extend(response.json())
            return json_values
        else:
            return self.http_responses.json()

    def get_output(self):
        return [result['value'] for result in self.json if 'value' in result and result['value']]
