import time
import datetime
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils_int.lib.profile_flows.flowprofile import FlowProfile


class CmImport15Flow(FlowProfile):

    TIMEOUT = 60 * 60 * 8

    def execute_flow(self):
        """
        Execute the flow of cmimport_15
        """
        users = self.create_users(number=self.NUM_USERS, roles=self.USER_ROLES, fail_fast=False, retry=True)

        self.state = "RUNNING"
        while self.keep_running():
            self.sleep_until_time()
            try:
                timeout_time = datetime.datetime.now() + datetime.timedelta(seconds=self.TIMEOUT)

                while datetime.datetime.now() < timeout_time:
                    self.request_first_fifty_jobs(users)
                    time.sleep(20)

            except Exception as e:
                self.add_error_as_exception(e)

    @staticmethod
    def request_first_fifty_jobs(users):
        """
        Request the first 50 import jobs for each user in the list of users
        :param users: list of users to make requests
        :type users: list
        """

        request_50_jobs_endpoint = (
            'bulk-configuration/v1/import-jobs/jobs/?offset=0&limit=50&expand=summary&expand=failures&createdBy={user}')

        for user in users:
            response = user.get(url=request_50_jobs_endpoint.format(user=user))
            raise_for_status(response, message_prefix='Could not retrieve first 50 jobs for user {0}'.format(user))
