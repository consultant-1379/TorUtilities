from requests.exceptions import RequestException

from enmutils.lib import headers, log, persistence
from enmutils.lib.cache import is_enm_on_cloud_native
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class CmEventsNbi01(GenericFlow):

    def execute_flow(self):
        self.state = "RUNNING"
        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
        if is_enm_on_cloud_native() and persistence.get("network-type") == "five_k_network":
            self.EVENT_LIMIT = 5000  # pylint: disable=W0201

        while self.keep_running():
            self.create_and_execute_threads(users, len(users), args=[self], last_error_only=True)
            self.sleep()

    @staticmethod
    def task_set(worker, profile):
        """
        Method to make the REST request

        :type worker: `enm_user_2.User`
        :param worker: User who will make the GET request
        :type profile: `flow_profile.FlowProfile`
        :param profile: limit for each user consuming events
        """
        log.logger.debug("Retrieving events from cm events nbi.")
        try:
            response = worker.get(profile.URL.format(limit=profile.EVENT_LIMIT),
                                  headers=headers.SECURITY_REQUEST_HEADERS, timeout=60, stream=True)
            raise_for_status(response, message_prefix="Failed to retrieve events: ")
            log.logger.debug("Successfully retrieved events from cm events nbi.")
        except RequestException as e:
            profile.add_error_as_exception(e)
