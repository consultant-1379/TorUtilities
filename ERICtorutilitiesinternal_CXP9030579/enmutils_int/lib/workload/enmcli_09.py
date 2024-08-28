from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.cmcli import execute_command_on_enm_cli
from enmutils.lib import log
from enmutils.lib.exceptions import NoNodesAvailable, EnvironError


class ENMCLI_09(GenericFlow):
    """
        Use Case ID:    ENMCLI_09
        Slogan:         CM CLI Read For YANG Nodes
        """
    NAME = "ENMCLI_09"
    READ_COMMAND = 'cmedit get {nodes_string} "asymmetric-key$$cmp".*'

    def run(self):
        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]

        self.state = "RUNNING"

        while self.keep_running():
            self.sleep_until_next_scheduled_iteration()

            try:
                nodes_list = self.get_nodes_list_by_attribute(['node_id', 'node_name', 'subnetwork'])
                cucp_nodes_list = [node.node_name for node in nodes_list]
                log.logger.info("cucp_node_name_list is {0}".format(cucp_nodes_list))
                if cucp_nodes_list:
                    response = execute_command_on_enm_cli(user, self.READ_COMMAND.format(nodes_string=';'.join(cucp_nodes_list)))
                    log.logger.debug("output of enmcli read command on cucp nodes is {0}".format(response.get_output()))
                    no_of_instances = response.get_output()[-1].split(" ")[0] if "instance(s)" in response.get_output()[-1] else ' '
                    if str(len(cucp_nodes_list)) != no_of_instances:
                        raise EnvironError("Failed to execute cm cli read command on few of the available nodes")
                    else:
                        log.logger.info("Execution of CM CLI read command on all available CUCP nodes is successful")
                else:
                    raise NoNodesAvailable('No CUCP nodes are available in server for enmcli_09')
            except Exception as e:
                self.add_error_as_exception(e)


enmcli_09 = ENMCLI_09()
