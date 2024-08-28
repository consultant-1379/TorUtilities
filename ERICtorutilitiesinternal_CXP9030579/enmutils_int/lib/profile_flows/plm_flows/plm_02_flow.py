import json
from functools import partial
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError
from enmutils.lib.persistence import picklable_boundmethod


class Plm02Flow(GenericFlow):
    DISCOVER_LINK_URL = "linkmanagerservice/linkmanager/reDiscoverLinks"
    DELETE_DISCOVERED_URL = "linkmanagerservice/linkmanager/deleteDiscoveredLinks"
    LIST_NODES = []
    JSON_SECURITY_REQUEST = {"X-Requested-With": "XMLHttpRequest", "Content-Type": "application/json",
                             "Accept": "application/json"}
    TEARDOWN = []
    RESET = 2
    FLAG = True

    def execute_flow(self):
        """
        Executes the flow for PLM_02 use case
        """
        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]
        teardown_list = self.teardown_list
        teardown_list.append(user)
        self.state = "RUNNING"

        while self.keep_running():
            try:
                allocated_nodes = self.get_nodes_list_by_attribute()
                self.LIST_NODES = [node.node_id for node in allocated_nodes]
                if not self.LIST_NODES:
                    raise EnvironError("No Nodes are allocated for profile to discover the links")
                if self.FLAG:
                    self.rediscovery_of_links(user, self.LIST_NODES)
                    self.TEARDOWN = partial(picklable_boundmethod(self.delete_discovered_links), user, self.LIST_NODES)
                    teardown_list.append(self.TEARDOWN)
                    log.logger.debug("Profile will be sleeping for 30 minutes before performing Delete discovery "
                                     "operation")
                    self.FLAG = False
                else:
                    self.delete_discovered_links(user, self.LIST_NODES)
                    teardown_list.remove(self.TEARDOWN)
                    log.logger.debug("Profile will be sleeping for 30 minutes before performing discovery of links "
                                     "operation on new set of nodes")
                    self.FLAG = True
                self.sleep()
                self.RESET -= 1
                if self.RESET == 0:
                    log.logger.debug("Performing Exchange of Nodes")
                    self.exchange_nodes()
                    self.RESET = 2
            except Exception as e:
                self.add_error_as_exception(e)

    def rediscovery_of_links(self, user, node_list):
        """
        Discovers links on 20 nodes
        :param user: user
        :type user: user object
        :param node_list: list of nodes on which links will be discovered
        :type node_list: list

        :raises EnvironError: when post request fails
        """
        log.logger.debug("Sending request for Discovering links for the nodes : {0}".format(node_list))
        payload = {"nodeNamesList": node_list, "jobId": "69d2de8a-bad6-a807-3db4-2da825f7ca71-1684479702187"}
        log.logger.debug("payload data : {0}".format(payload))
        response = user.post(self.DISCOVER_LINK_URL, data=json.dumps(payload), headers=self.JSON_SECURITY_REQUEST)
        if response.ok:
            log.logger.debug("Successfully discovered links on {0} MINI_LINK_669x nodes".format(len(node_list)))
        else:
            raise EnvironError("Failed to discover links : {0}".format(response))

    def delete_discovered_links(self, user, node_list=None):
        """
        Deletes discovered links on 20 nodes
        :param user: user
        :type user: user object
        :param node_list: list of nodes on which links will be discovered
        :type node_list: list

        :raises EnvironError: when post request fails
        """
        log.logger.debug("Sending request for Deleting Discovered links for the nodes : {0}".format(node_list))
        response = user.post(self.DELETE_DISCOVERED_URL, data=json.dumps(node_list), headers=self.JSON_SECURITY_REQUEST)
        if response.ok:
            log.logger.debug("Successfully deleted discovered links on {0} MINI_LINK_669x nodes".format(len(node_list)))
        else:
            raise EnvironError("Failed to delete discovered links : {0}".format(response))
