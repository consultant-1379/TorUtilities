import random
import time

from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError, EnvironError

from enmutils_int.lib.cmcli import execute_command_on_enm_cli
from enmutils_int.lib.common_utils import chunks
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class EnmCli06Flow(GenericFlow):
    CMD_TO_UPDATE = ("cmedit set SubNetwork=NETSimG,MeContext={0},ManagedElement={0},"
                     "BscFunction=1,BscM=1,Bts=1 linkCheckTime={1}")

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        self.state = "RUNNING"
        users = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)
        nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "node_name"])
        user_node_data = zip(users, chunks(nodes, self.NUM_COMMANDS))
        if user_node_data:
            while self.keep_running():
                self.sleep_until_time()
                self.create_and_execute_threads(user_node_data, len(users), args=[self],
                                                wait=self.THREAD_QUEUE_TIMEOUT)
        else:
            self.add_error_as_exception(
                EnvironError("Could not form the data containing user and corresponding commands "
                             "due to unavailability of either users or required nodes"))

    @staticmethod
    def task_set(worker, profile):
        """
        Flow to be used to run this profile
        :param worker:  list of users
        :type worker:   list
        :param profile: Profile object
        :type profile:  `enmutils_int.lib.profile.Profile`
        """
        user, nodes_per_user = worker
        values_to_update = xrange(profile.NUM_COMMANDS + 1)
        for node in nodes_per_user:
            try:
                execute_command_on_enm_cli(user, command=profile.CMD_TO_UPDATE.format(
                    node.node_name, random.sample(values_to_update, 1)[0]), timeout=600)
            except Exception as e:
                profile.add_error_as_exception(EnmApplicationError(e))
            log.logger.info("Waiting for 3 minutes for the next command by the user")
            time.sleep(180)
