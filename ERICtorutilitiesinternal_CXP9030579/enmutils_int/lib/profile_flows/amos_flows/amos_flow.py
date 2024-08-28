from enmutils.lib import log
from enmutils.lib.arguments import grouper
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.amos_executor import (construct_command_list, check_ldap_is_configured_on_radio_nodes,
                                            get_radio_erbs_nodes)


class AmosCommonFlow(GenericFlow):

    COMMANDS_LIST = []
    USER_NODES = []

    def perform_amos_prerequisites(self, users, nodes):
        """
        Executes pre-requisite steps for the amos profiles like creating PKI entities and configuring ldap on RadioNodes
        :param users: ENM users created by the profile
        :type users: list
        :param nodes: Nodes allocated to the profile
        :type nodes: list
        """
        radio_nodes, erbs_nodes = get_radio_erbs_nodes(nodes)
        self.download_tls_certs(users)
        try:
            configured_radio_nodes = check_ldap_is_configured_on_radio_nodes(self, users[0], radio_nodes, self.NAME)
        except Exception as e:
            configured_radio_nodes = radio_nodes
            self.add_error_as_exception(e)

        total_nodes = erbs_nodes + configured_radio_nodes

        no_lt_all_commands = construct_command_list(self.COMMANDS, self.COMMANDS_PER_ITERATION)
        self.COMMANDS_LIST = ["lt all"] + no_lt_all_commands
        log.logger.debug('Number of commands per user for this iteration : {}'.format(len(self.COMMANDS_LIST)))
        node_tuples = grouper(total_nodes, 1)

        if self.NAME == "AMOS_05":
            self.USER_NODES = zip(users, node_tuples)
        else:
            sleep_distribution = range(0, len(total_nodes) * 2, 2)
            self.USER_NODES = zip(users, node_tuples, sleep_distribution)
            log.logger.debug('Initial nodes_tuples: {0}'.format(len(self.USER_NODES)))
            log.logger.debug('Initial number of nodes: {0}'.format(len(total_nodes)))
            log.logger.debug('Initial number of users: {0}'.format(len(users)))
            log.logger.debug('Initial sleep in minutes: {0}'.format(len(sleep_distribution)))
