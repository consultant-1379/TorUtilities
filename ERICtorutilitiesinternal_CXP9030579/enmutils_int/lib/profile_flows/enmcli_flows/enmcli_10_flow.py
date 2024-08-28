import time
from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.cmcli import execute_command_on_enm_cli
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow

CLI_SET_COMMAND = 'cmedit set {0} "asymmetric-key$$cmp" renewal-mode={1}'


class ENMCLI10Flow(GenericFlow):

    def execute_flow(self):
        """
        Executes the Main flow for ENMCLI_10 profile
        """
        self.state = "RUNNING"
        user = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)[0]
        nodes = self.get_nodes_list_by_attribute()
        while self.keep_running():
            self.sleep_until_time()
            try:
                self.execute_and_validate_response(user, nodes, "manual")
                log.logger.debug("Sleeping for 300 seconds before setting renewal-mode to automatic")
                time.sleep(300)
                self.execute_and_validate_response(user, nodes, "automatic")

            except Exception as e:
                self.add_error_as_exception(e)

    def execute_and_validate_response(self, user, nodes, mode):
        """
        Checks if the number of instances in the output matches the number of nodes
        :param user: enm user
        :type user: instance of enm_user_2
        :param nodes: list of nodes
        :type nodes: list
        :param mode: value of renewal mode
        :type mode: str

        :raises EnmApplicationError: raised if execution in cli fails for a few nodes
        """
        nodes_string = ';'.join([node.node_id for node in nodes])
        response = execute_command_on_enm_cli(user, CLI_SET_COMMAND.format(nodes_string, mode))
        output = response.get_output()
        no_of_instances = int(output[-1].split(" ")[0]) if "instance" in output[-1] else 0
        if len(nodes) != no_of_instances:
            raise EnmApplicationError("Execution on cli failed for a few nodes. O/P: {0}".format(output))
        log.logger.debug("Attribute renewal-mode set to {0} for {1} nodes. O/P: {2}".format(mode, len(nodes), output))
