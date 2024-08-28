import random
from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError, SessionNotEstablishedException, EnvironError
from enmutils_int.lib.amos_executor import (set_max_amos_sessions, taskset, check_ldap_is_configured_on_radio_nodes,
                                            delete_user_sessions, get_radio_erbs_nodes)
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class AMOS_08(GenericFlow):
    """
    Use Case id:        AMOS_08
    Slogan:             Launch AMOS in Shell Terminal and run commands on multiple nodes in parallel.
    """

    NAME = "AMOS_08"

    def run(self):
        set_max_amos_sessions(self, self.MAX_AMOS_SESSIONS)
        users = self.create_users(self.NUM_USERS, self.USER_ROLES, fail_fast=False, retry=True)
        nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "subnetwork", "primary_type", "node_ip"])
        radio_nodes, erbs_nodes = get_radio_erbs_nodes(nodes)

        self.download_tls_certs(users)
        try:
            configured_radio_nodes = check_ldap_is_configured_on_radio_nodes(self, users[0], radio_nodes, self.NAME)
        except Exception as e:
            configured_radio_nodes = radio_nodes
            self.add_error_as_exception(e)

        total_nodes = erbs_nodes + configured_radio_nodes
        node_tuples = random.sample(total_nodes, 1)
        user_nodes = (users[0], node_tuples, 0)

        self.state = "RUNNING"

        while self.keep_running():
            self.sleep_until_time()
            log.logger.debug('Iteration began running')
            try:
                taskset(user_nodes, self.COMMANDS, self.VERIFY_TIMEOUT)
            except Exception as e:
                self.add_error_as_exception(e)
            try:
                delete_user_sessions(users)
            except SessionNotEstablishedException as e:
                self.add_error_as_exception(EnvironError(e))
            except Exception as e:
                self.add_error_as_exception(EnmApplicationError(e))
            log.logger.debug('Iteration finished running')


amos_08 = AMOS_08()
