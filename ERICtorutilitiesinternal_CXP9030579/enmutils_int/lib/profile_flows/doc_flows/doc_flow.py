import time
import random

from enmutils_int.lib.alex_doc import get_doc_url, DOC_SERVICE, URLS_TO_VISIT
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils.lib import log


class Doc01Flow(GenericFlow):

    def execute_flow(self):
        """
        Main flow for DOC_01
        """

        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES, safe_request=True)
        self.state = "RUNNING"
        while self.keep_running():
            self.create_and_execute_threads(users, len(users), args=[self], wait=60 * 25, join=60 * 25)
            self.sleep()

    @staticmethod
    def task_set(worker, profile):
        """
        The task set for thread queues
        :param worker: The user that navigates on the UI launcher
        :type worker: enmutils.lib.enm_user_2.User
        :param profile: Profile to add errors to
        :type profile: `flowprofile.FlowProfile`
        """
        user = worker

        try:
            log.logger.debug("Access homepage for documentation.")
            get_doc_url(user, '/{0}'.format(DOC_SERVICE))
            rand_sleep = random.randint(1, 5)
            log.logger.debug("Access a random page after randomly "
                             "sleeping for {0} seconds.".format(rand_sleep))
            time.sleep(rand_sleep)
            get_doc_url(user, random.choice(URLS_TO_VISIT))
            log.logger.debug("Navigate away to close documentation.")
            get_doc_url(user, '#launcher/groups')
        except Exception as e:
            profile.add_error_as_exception(e)
