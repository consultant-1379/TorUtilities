import datetime
import json

from enmutils.lib import log
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils.lib.headers import JSON_SECURITY_REQUEST
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class LauncherFlow(GenericFlow):
    requests = []

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        self.state = 'RUNNING'
        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
        while self.keep_running():
            end_time = self.get_end_time()
            while datetime.datetime.now() <= end_time:
                self.request_handler(users)
                self.sleep()

    def request_handler(self, users):
        """
        Sends requests based on requests defined by profile
        :param users: List of enm users that makes the requests
        :type users: list
        """
        successful_requests = 0
        for user in users:
            for request in self.requests:
                try:
                    method, end_point, json_data = request
                    request = getattr(user, method)
                    response = request(end_point, data=json.dumps(json_data), headers=JSON_SECURITY_REQUEST)
                    raise_for_status(response)
                    successful_requests += 1
                except Exception as e:
                    self.add_error_as_exception(e)
        log.logger.debug("Successful requests: {0}/{1}".format(successful_requests, len(users) * len(self.requests)))


class LauncherFlow01(LauncherFlow):
    json_data = {
        "application": "networkexplorer",
        "multipleSelection": "false",
        "conditions": [{
            "dataType": "ManagedObject",
            "properties": [{"name": "type", "value": "MeContext"},
                           {"name": "neType", "value": "ERBS"}]
        }]
    }
    endpoint = "/rest/v1/apps/action-matches"
    requests = [("post", endpoint, json_data)]


class LauncherFlow02(LauncherFlow):
    endpoints = ["/rest/system/time", "/rest/system/v1/name", "/rest/groups"]
    requests = [("get", endpoints[0], None), ("get", endpoints[1], None), ("get", endpoints[2], None)]


class LauncherFlow03(LauncherFlow):
    set_favorite = {
        "id": "alex",
        "value": "true"
    }
    remove_favorite = {
        "id": "alex",
        "value": "false"
    }
    endpoint = "/rest/ui/settings/launcher/favorites"
    requests = [("put", endpoint, set_favorite), ("put", endpoint, remove_favorite)]
