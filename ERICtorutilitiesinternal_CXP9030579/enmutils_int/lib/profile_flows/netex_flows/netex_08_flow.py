from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError

READ_CMD = 'cmedit get {node_name} "modules-state$$module".*'


class Netex08Flow(GenericFlow):

    def execute_flow(self):
        """
        Executes the Main flow for Netex_08 profile
        """
        self.state = "RUNNING"
        user = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)[0]
        nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "netsim", "simulation",
                                                                  "primary_type", "node_name"])
        vcucp_node_names = [node.node_id for node in nodes]
        if not vcucp_node_names:
            raise EnmApplicationError("No Nodes of vCUCP type are available in this deployment")
        while self.keep_running():
            self.sleep_until_day()
            try:
                self.create_and_execute_threads(vcucp_node_names, len(vcucp_node_names), args=[self, user])
            except Exception as e:
                self.add_error_as_exception(e)

    @staticmethod
    def task_set(vcucp_node_names, profile, user):  # pylint: disable=arguments-differ
        """
        Executes cmedit commands and display response
        :param vcucp_node_names: nodes to be executed
        :type vcucp_node_names: list
        :param profile: Profile object.
        :type profile: 'profile.Profile'
        :param user: user is used to execute command
        :type user: enm_user.User object
        """
        try:
            cmd = READ_CMD.format(node_name=vcucp_node_names)
            response = user.enm_execute(cmd)
            output = response.get_output()
            instance = int(str(output[len(output) - 1]).split(' ')[0])
            if instance == 0:
                profile.add_error_as_exception(
                    EnmApplicationError(
                        "No of instances for node {0} is {1}".format(vcucp_node_names, output[len(output) - 1])))
            else:
                log.logger.debug(
                    "No of instances for node {0} is {1}".format(vcucp_node_names, output[len(output) - 1]))
        except Exception as e:
            log.logger.debug("Exception caught while executing cmedit command : {0}".format(e))
