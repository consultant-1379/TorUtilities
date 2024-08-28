import time
from datetime import datetime, timedelta
from enmutils.lib.headers import JSON_SECURITY_REQUEST
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib import log
from enmutils_int.lib import load_mgr
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow

ENERGY_REPORT = "/sev/v1/energy-report?poIds={0}&periods="
ENERGY_FLOW = "/sev/v1/energy-flow?poId={0}"


class SEV01Flow(GenericFlow):

    def execute_flow(self):
        """
        Executes the Main flow for SEV_01 profile
        """
        self.state = "RUNNING"
        users = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)
        while self.keep_running():
            try:
                nodes_list = self.get_nodes_list_by_attribute(node_attributes=['node_id', 'poid'])
                if nodes_list:
                    nodes_users_info = zip(nodes_list, users)
                    self.create_and_execute_threads(nodes_users_info, len(nodes_users_info), args=[self])
                    self.exchange_nodes()
                else:
                    raise EnmApplicationError("No synced nodes available for this iteration")
            except Exception as e:
                self.add_error_as_exception(e)
            self.sleep()

    @staticmethod
    def task_set(node_user_info, profile):
        """
        :param node_user_info:node_user_info is the list of users and nodes.
        :type node_user_info: list
        :param profile: Profile object.
        :type profile: 'profile.Profile'
        :raises EnmApplicationError: if there is error in response from ENM
        """
        try:
            node = node_user_info[0]
            user = node_user_info[1]
            log.logger.debug("User : {0} , poId : {1}".format(user, node.poid))
            start = time.time()
            url = ENERGY_FLOW.format(node.poid)
            response = user.get(url, headers=JSON_SECURITY_REQUEST)
            log.logger.debug('Elapsed time for the request {0} is : {1}'.format(url, time.time() - start))
            if response.status_code != 200 and response.status_code != 429:
                log.logger.debug("The request was unsuccessful with the node: {0}".format(node.node_id))
                response.raise_for_status()
            log.logger.debug("Response : {0}".format(response.json()))
        except Exception as e:
            profile.add_error_as_exception(e)


class SEV02Flow(GenericFlow):

    def execute_flow(self):
        """
        Executes the Main flow for SEV_02 profile
        """
        self.state = "RUNNING"
        load_mgr.wait_for_setup_profile("SEV_01", state_to_wait_for="SLEEPING")
        users = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)
        while self.keep_running():
            try:
                nodes_list = self.get_nodes_list_by_attribute(node_attributes=['node_id', 'poid'])
                if nodes_list:
                    nodes_users_info = zip(nodes_list, users)
                    self.create_and_execute_threads(nodes_users_info, len(nodes_users_info), args=[self])
                    self.exchange_nodes()
                else:
                    raise EnmApplicationError("No synced nodes available for this iteration")
            except Exception as e:
                self.add_error_as_exception(e)
            self.sleep()

    @staticmethod
    def task_set(node_user_info, profile):
        """
        :param node_user_info:node_user_info is the list of users and nodes.
        :type node_user_info: list
        :param profile: Profile object.
        :type profile: 'profile.Profile'
        :raises EnmApplicationError: if there is error in response from ENM
        """
        try:
            node = node_user_info[0]
            user = node_user_info[1]
            log.logger.debug("User : {0} , poId : {1}".format(user, node.poid))
            start = time.time()
            now = datetime.now()
            dates = ",".join([(now - timedelta(days=x)).strftime("%d/%m/%Y") for x in range(8)])
            url = ENERGY_REPORT.format(node.poid) + dates
            response = user.get(url, headers=JSON_SECURITY_REQUEST)
            log.logger.debug('Elapsed time for the request {0} is : {1}'.format(url, time.time() - start))
            if response.status_code != 200 and response.status_code != 429:
                log.logger.debug("The request was unsuccessful with the node: {0}".format(node.node_id))
                response.raise_for_status()
            log.logger.debug("Response : {0}".format(response.json()))
        except Exception as e:
            profile.add_error_as_exception(e)
