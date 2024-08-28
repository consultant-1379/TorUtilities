import time

from enmutils.lib import log
from enmutils_int.lib.dynamic_crud import DYNAMIC_CRUD_02_CMD_LIST
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow

NUM_THREADS = 3


class DynamicCrud02Flow(GenericFlow):

    def execute_flow(self):
        """
        Executes the flow
        """
        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]
        self.state = "RUNNING"
        while self.keep_running():
            self.create_and_execute_threads(DYNAMIC_CRUD_02_CMD_LIST, NUM_THREADS, func_ref=self.tasks_set,
                                            args=[self, user])
            self.sleep()
            log.logger.debug("Re-establish user session and then wait for 10 seconds.")
            user.open_session(reestablish=True)
            time.sleep(10)

    @staticmethod
    def tasks_set(worker, profile, user):
        """
        Method to make the REST request

        :param worker: list of commands to be executed
        :type worker: list
        :param profile: Profile object to execute the functionality
        :type profile: `flow_profile.FlowProfile`
        :param user: User who will make the GET request
        :type user: `enm_user_2.User`
        """

        cmd, number_of_times = worker
        for _ in range(number_of_times):
            profile.get_given_url(user, cmd)

    def get_given_url(self, user, url):
        """
        Perform GET request on given URL

        :param user: User who will make the requests
        :type user: `enm_user_2.User`
        :param url: URL of the request
        :type url: str
        """
        try:
            response = user.get(url)
            response.raise_for_status()
        except Exception as e:
            self.add_error_as_exception(e)
