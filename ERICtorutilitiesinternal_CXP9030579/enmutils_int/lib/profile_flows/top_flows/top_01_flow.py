import time

from requests import ConnectionError, HTTPError

from enmutils.lib import log, multitasking
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils_int.lib.netex import Search, get_pos_by_poids
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.topology_browser import (
    step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd,
    update_random_attribute_on_eutrancellfdd_or_eutrancelltdd,
    navigate_topology_browser_app_help, step_through_topology_browser_node_tree_to_nrcelldu,
    update_random_attribute_on_nrcelldu, step_through_topology_browser_node_tree_to_nrcellcu,
    update_random_attribute_on_nrcellcu)


class TOP01Flow(GenericFlow):
    def execute_flow(self):
        """
        Executes the profiles flow
        """
        try:
            users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
            setup_user = users[0]
            mecontext_subnetworks = Search(user=setup_user,
                                           query="SubNetwork where object SubNetwork has child MeContext",
                                           version="v2").execute()
            managed_element_subnetworks = Search(user=setup_user,
                                                 query="SubNetwork where object SubNetwork has child ManagedElement",
                                                 version="v2").execute()
            subnw_dict = {}
            mecontext_subnw_dict = self.get_subnetwork_poids_and_names(setup_user, mecontext_subnetworks)
            managed_element_subnw_dict = self.get_subnetwork_poids_and_names(setup_user, managed_element_subnetworks)
            subnw_dict.update(mecontext_subnw_dict)
            subnw_dict.update(managed_element_subnw_dict)
            self.state = "RUNNING"
            while self.keep_running():
                nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "subnetwork_id",
                                                                          "managed_element_type"])
                try:
                    if nodes:
                        nodes_with_subnet_poids, num_of_subnetworks = self.get_subnetwork_poid_per_node(users[0], nodes, subnw_dict)

                        if not nodes_with_subnet_poids:
                            self.add_error_as_exception(
                                EnmApplicationError("No nodes were found on any sub-network. Please check "
                                                    "HTTP requests / network topology. Trying again next "
                                                    "iteration"))
                        elif len(users) != len(nodes_with_subnet_poids):
                            self.add_error_as_exception(EnmApplicationError("Length of nodes_with_subnet_poids: {0}, "
                                                                            "num of users: {1}"
                                                                            .format(len(nodes_with_subnet_poids),
                                                                                    len(users))))
                        if nodes_with_subnet_poids:
                            user_nodes_list = zip(users, nodes_with_subnet_poids)
                            multitasking.create_single_process_and_execute_task(execute_user_tasks,
                                                                                args=(self, user_nodes_list, len(users),
                                                                                      num_of_subnetworks, self.THREAD_QUEUE_TIMEOUT),
                                                                                timeout=60 * 60)
                    else:
                        raise EnvironError('Check whether synced nodes are available or not in the deployment')
                except Exception as e:
                    self.add_error_as_exception(EnmApplicationError(e))
                log.logger.debug("Waiting for 15 minutes at the end of the iteration.")
                time.sleep(15 * 60)

                # change the nodes.
                self.exchange_nodes()
        except (HTTPError, ConnectionError, EnmApplicationError) as e:
            self.add_error_as_exception(EnmApplicationError(str(e)))
            log.logger.debug(
                "Issue encountered in setting up pre-requisites. Please restart the profile when the environment is stable.")

    @staticmethod
    def get_subnetwork_poids_and_names(user, search):
        """
        Get poid and name for sub-networks with child MeContext or ManagedElement

        :param user: user to execute get request
        :type user: `enmutils.lib.enm_user_2.User`
        :param search: search response for sub-networks
        :type search: dict
        :return: poid and name for sub-networks
        :rtype: dict
        """
        subnetwork_poids = [subnetwork_object["id"] for subnetwork_object in search["objects"]]
        subnetwork_po_data = get_pos_by_poids(user, subnetwork_poids,
                                              [{"moType": "SubNetwork", "attributeNames": []}]).json()
        return {subnw["poId"]: subnw["moName"] for subnw in subnetwork_po_data}

    @staticmethod
    def task_set(user_to_node_info_list, num_of_subnetworks):  # pylint: disable=arguments-differ
        """
        UI Flow to be used to run this profile

        :param user_to_node_info_list: list with user and unique node {user : node}
        :type user_to_node_info_list: list
        :param num_of_subnetworks: number of sub-networks
        :type num_of_subnetworks: int
        """
        user = user_to_node_info_list[0]
        node_subnet = user_to_node_info_list[1]
        user_index = int(user.username.split("_u")[1])
        timeout = user_index * 15
        time.sleep(timeout)
        node_id = node_subnet[0]
        node_poid = node_subnet[1]
        subnetwork_poid = node_subnet[2]
        managed_element_type = node_subnet[3]

        log.logger.debug("User: {0} Using node ({1})".format(user.username, node_id))

        if user_index not in range(1,
                                   num_of_subnetworks + 1):  # we have already made this call above n times: n = number of subnetworks.
            node_mos_from_subnetwork_request = user.get("/persistentObject/network/{0}".format(subnetwork_poid))
            time.sleep(1)
            node_mos_from_subnetwork_request.raise_for_status()

        # For GNodeB function
        if managed_element_type == 'GNodeB':
            nrcelldu_attributes = step_through_topology_browser_node_tree_to_nrcelldu(user, node_poid, node_id)

            modified_attribute_default_value = update_random_attribute_on_nrcelldu(nrcelldu_attributes, user)
            time.sleep(60 * 5)
            update_random_attribute_on_nrcelldu(nrcelldu_attributes, user,
                                                attribute_default=modified_attribute_default_value, action="UNDO")
        # For NodeB or ENodeB function
        elif managed_element_type == 'ENodeB' or managed_element_type == 'NodeB':
            eutrancell_attributes = step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd(user,
                                                                                                              node_poid,
                                                                                                              node_id)
            modified_attribute_default_value = update_random_attribute_on_eutrancellfdd_or_eutrancelltdd(eutrancell_attributes, user)
            time.sleep(60 * 5)
            update_random_attribute_on_eutrancellfdd_or_eutrancelltdd(eutrancell_attributes, user,
                                                                      attribute_default=modified_attribute_default_value,
                                                                      action="UNDO")

        else:
            nrcellcu_attributes = step_through_topology_browser_node_tree_to_nrcellcu(user, node_poid, node_id)

            modified_attribute_default_value = update_random_attribute_on_nrcellcu(nrcellcu_attributes, user)
            time.sleep(60 * 5)
            update_random_attribute_on_nrcellcu(nrcellcu_attributes, user,
                                                attribute_default=modified_attribute_default_value, action="UNDO")

        navigate_topology_browser_app_help(user)

    def get_subnetwork_poid_per_node(self, user, nodes, subnetwork_poids_names):
        """
        Create a list of tuples of nodes with their subnetwork poid.

        :param user: user to execute get request
        :type user: `enmutils.lib.enm_user_2.User`
        :param nodes: list nodes
        :type nodes: list
        :param subnetwork_poids_names: dict of sub-network po ids and names
        :type subnetwork_poids_names: dict
        :return: list of tuples of nodes and sub-network poid, number of sub-networks
        :rtype: tuple
        :raises EnmApplicationError: If user cannot establish the session to get the node poids
        """
        nodes_with_subnet_poids = []
        node_name_poids = {}

        if not user.is_session_established():
            raise EnmApplicationError("User is unable to login to ENM, please check the profile log for more details")

        for sub_net_poid, subnet_name in subnetwork_poids_names.iteritems():
            try:
                log.logger.debug("Obtaining node poids from network : {0}".format(subnet_name))
                node_mos_from_subnetwork_request = user.get("/persistentObject/network/{0}".format(sub_net_poid))
                node_mos_from_subnetwork_request.raise_for_status()
                time.sleep(5)
            except Exception as e:
                self.add_error_as_exception(EnmApplicationError(str(e)))
            else:
                node_mos_from_subnetwork = node_mos_from_subnetwork_request.json()
                node_name_poids.update({node_mo['moName']: node_mo['poId'] for node_mo in
                                        node_mos_from_subnetwork['treeNodes'][0]['childrens']})

        for node in nodes:
            nodes_with_subnet_poids = self.update_nodes_with_subnet_poids(node, subnetwork_poids_names,
                                                                          node_name_poids, nodes_with_subnet_poids)

        return nodes_with_subnet_poids, len(subnetwork_poids_names)

    def update_nodes_with_subnet_poids(self, node, subnetwork_poids_names, node_name_poids, nodes_with_subnet_poids):
        """
        Update the list of node name, node poid and sub-network poid tuples
        if the node is present in the sub-network

        :param node: Node objects
        :type node: `enmutils.lib.enm_node.Node`
        :param subnetwork_poids_names: Sub-network poid and names
        :type subnetwork_poids_names: dict
        :param node_name_poids: Node name and poid
        :type node_name_poids: dict
        :param nodes_with_subnet_poids: List of Node name, node poid and sub-network poid tuples
        :type nodes_with_subnet_poids: list
        :return: List of Node name, node poid and sub-network poid tuples
        :rtype: list
        """
        node_not_found_msg = "Node {node} not found on SubNetwork".format(node=node.node_id)
        if node.node_id in node_name_poids.keys():
            key_for_subnw = None
            for key, value in subnetwork_poids_names.items():
                if node.subnetwork_id == value:
                    key_for_subnw = key
                    break
            if key_for_subnw:
                subnet_poid = key_for_subnw
                node_poid = node_name_poids[node.node_id]
                nodes_with_subnet_poids.append([node.node_id, node_poid, subnet_poid, node.managed_element_type])
                log.logger.debug("Node {0} in SubNetwork with poId: {1}".format(node.node_id, subnet_poid))
            else:
                log.logger.debug(node_not_found_msg)
        else:
            log.logger.debug(node_not_found_msg)

        return nodes_with_subnet_poids


def execute_user_tasks(profile, user_to_node_info_list, user_count, num_of_subnetworks, thread_timeout):
    """
    Executes all the user tasks as a separate process (to reduce memory consumption)
    :param profile: TOP_01 Profile object
    :type profile: TOP_01 Profile
    :param user_to_node_info_list: list with user and unique node {user : node}
    :type user_to_node_info_list: list
    :param user_count: Number of users
    :type user_count: int
    :param num_of_subnetworks: number of subnetworks
    :type num_of_subnetworks: int
    :param thread_timeout: Timeout for each thread
    :type thread_timeout: int
    """
    profile.create_and_execute_threads(workers=user_to_node_info_list, thread_count=user_count, args=[num_of_subnetworks],
                                       wait=thread_timeout, join=thread_timeout)
