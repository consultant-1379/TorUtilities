# ********************************************************************
# Name    : Log Viewer
# Summary : Primary module used to interact with ENM Logviewer
#           application. Allows the user to search the Logviewer and
#           views the resulting log entries.
# ********************************************************************

import json
import urllib
from enmutils.lib.exceptions import InvalidSearchError


class LogViewer(object):

    DEFAULT_URL = "/#logviewer"
    SEARCH_URL = "/elasticsearch/enm_logs*/_search?sort=timestamp:desc&size=50&from=0&q="
    APP_HELP_URL = "/#help/app/logviewer"

    def __init__(self, user, search_term):
        """
        Constructor for ENM Role object

        :type search_term: str
        :param search_term: The search term to filter the log files by
        :type user : enm_user.User object
        :param user: user we use to create the Role
        """
        self.search_term = search_term if search_term else None
        self.user = user
        self.security_request_headers = json.loads('{"X-Requested-With": "XMLHttpRequest"}')

    def get_log_viewer(self):
        """
        Get log viewer application

        :raises: HTTPError
        :rtype: status_code
        :returns: response.status_code
        """

        response = self.user.get(self.DEFAULT_URL, headers=self.security_request_headers)

        if response.status_code != 200:
            response.raise_for_status()

        return response.status_code

    def get_log_viewer_by_search_term(self):
        """
        Get filtered log viewer response

        :raises: HTTPError
        :rtype: list
        :returns: list of log entries filtered by a search term
        """
        if not self.search_term:
            raise InvalidSearchError("No valid search term provided.")
        url = "{0}{1}".format(self.SEARCH_URL, urllib.quote(self.search_term))
        response = self.user.get(url, headers=self.security_request_headers)
        if response.status_code != 200:
            response.raise_for_status()
        resp_list = json.loads(response.text)
        return resp_list

    def get_log_viewer_help(self):
        """
        Get app help

        :raises: HTTPError
        :rtype: status_code
        :returns: response.status_code
        """

        response = self.user.get(self.APP_HELP_URL, headers=self.security_request_headers)
        if response.status_code != 200:
            response.raise_for_status()

        return response.status_code
