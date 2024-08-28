from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.netex import search_and_save
from enmutils_int.lib.profile_flows.pm_flows.pmprofile import PmProfile
from enmutils_int.lib.pm_rest_nbi_subscriptions import Subscription
from enmutils_int.lib import node_pool_mgr
from enmutils_int.lib.services import nodemanager_adaptor


class PmSubscriptionProfile(PmProfile):
    """
    PM subscription profile flows superclass
    """

    USER = None
    NETEX_QUERY = None

    def set_nodes_from_netex_via_query(self, search, nodes):
        """
        Set nodes fetched from netex query

        :param search: Netex search object to execute search
        :type search: `netex.Search`
        :param nodes: List of nodes we want to add to collection
        :type nodes: list
        """

        log.logger.debug("Fetching nodes from netex query")
        try:
            node_mos = search.execute()
            setattr(self, "nodes_from_netex", [node for node in nodes if node.node_id in node_mos.keys()])
        except Exception as e:
            self.add_error_as_exception(e)

    def set_search_criteria(self):
        """
        Set search criteria

        If not in the system yet, save the criteria search.
        The node type query filter relies on the NUM_NODES dictionary profile attribute.

        :return List: The list contains a dictionary with the criteria search name and the netex query.
        """
        log.logger.debug("Setting the search criteria")
        nodes = self.all_nodes_in_workload_pool(node_attributes=["node_id", "poid", "primary_type"])
        ne_types = self.ENM_NE_TYPES if hasattr(self, 'ENM_NE_TYPES') else self.NUM_NODES.keys()
        saved_search, _ = search_and_save(self, self.USER,
                                          self.NETEX_QUERY.format(
                                              node_type=" or neType=".join(set(node_type for node_type in ne_types))),
                                          "{name}_cbs_subscription".format(name=self.NAME), nodes, delete_existing=True,
                                          version="v1", num_nodes=len(nodes))

        self.set_nodes_from_netex_via_query(saved_search, nodes)

        results = [{"name": saved_search.name, "criteriaIdString": saved_search.query}]
        log.logger.debug("Search criteria set: {0}".format(results))
        return results

    def set_values_from_cbs(self):
        """
        Set values provided by CBS flag on profile

        If the CBS flag value is activated, a criteria is set: if a netex query is not provided,
        the default one is used.
        If the CBS flag value is disabled, the netex query is ignored.

        :return type: Boolean. CBS flag value.
        :return type: List. With CBS on, the list contains a dictionary with the criteria search name and the netex
        query. Empty list otherwise.
        """
        if hasattr(self, 'CBS') and self.CBS:
            cbs = True
            if not self.NETEX_QUERY:
                self.NETEX_QUERY = 'select networkelement where neType = {node_type}'
            criteria = self.set_search_criteria()
        else:
            cbs = False
            criteria = []
            if self.NETEX_QUERY:
                log.logger.debug("A netex query has been provided but the subscription has not the CBS flag active."
                                 " The netex query will be ignored")
        return cbs, criteria

    def set_teardown(self, subscription_class, subscription_name, subscription_id, poll_scanners=False,
                     node_types=None):
        """
        Define teardown objects

        Create and add a smaller dummy subscription object to teardown list to reduce redis DB memory footprint of self.
        The dummy subscription has the name and the ID of the subscription that has to be eventually removed.

        :param subscription_class: Any of the classes used to create a subscription.
        :type subscription_class: class
        :param subscription_name: Name of the subscription to add to teardown.
        :type subscription_name: str
        :param subscription_id: ID of the subscription to add to teardown.
        :type subscription_id: int
        :param poll_scanners: Boolean to indicate is scanners should be checked when subscription is deactivated
        :type poll_scanners: bool
        :param node_types: profile allocated nodes types to check the scanners count while deactivate the subscription
        :type node_types: list

        """
        subscription_for_teardown = subscription_class(name=subscription_name, poll_scanners=poll_scanners,
                                                       node_types=node_types)
        subscription_for_teardown.id = subscription_id
        self.teardown_list.append(subscription_for_teardown)

    def set_subscription_description(self):
        """
        Define the subscription description using some of the profile attributes.

        :return String. The subscription description.
        """
        cbs_text = "cbs_" if hasattr(self, 'CBS') and self.CBS else ""
        subscription_description = "{0}_{1}load_profile".format(self.NAME, cbs_text)

        return subscription_description

    def execute_flow(self, **kwargs):
        """
        This method is inherited, run and extended by many sub-classes.
        If provided, retrieves the netex query value required by the profile. Set to 'None' otherwise.
        Creates appropriate users.

        """
        self.NETEX_QUERY = kwargs.pop('netex_query', None)

        log.logger.debug("Creating User")
        self.USER = self.create_users(1, roles=self.USER_ROLES, fail_fast=False, retry=True)[0]
        log.logger.debug("User created: {0}, having role(s): {1}".format(self.USER, self.USER_ROLES))
        log.logger.debug("Removing old {0} subscriptions which exist in ENM that have the same profile "
                         "name".format(self.NAME))
        Subscription.clean_subscriptions(name=self.NAME, user=self.USER)

    def delete_nodes_from_netex_attribute(self):
        """
        Helper method to delete netex generated nodes list
        """
        if hasattr(self, "nodes_from_netex"):
            delattr(self, "nodes_from_netex")

    def check_all_nodes_added_to_subscription(self, subscription):
        """
        Check that all allocated nodes got translated to parsed_nodes

        :param subscription: Subscription object
        :type subscription: enmutils_int.lib.pm_subscriptions.Subscription
        """
        if len(subscription.parsed_nodes) != len(subscription.nodes):
            self.add_error_as_exception(
                EnvironError("Some nodes ({0}) assigned to profile have not been added to "
                             "subscription after validity checks (e.g. PmFunction disabled etc)"
                             .format(len(subscription.nodes) - len(subscription.parsed_nodes))))

    def deallocate_and_update_nodes_count_for_profile(self, profile_nodes, cbs):
        """
        Deallocate profile allocated nodes and update profile_nodes count in profile persistence.

        :param profile_nodes: list of profile allocated nodes from workload pool
        :type profile_nodes: list
        :param cbs: CBS flag True, False
        :type cbs: bool
        """
        log.logger.debug("Deallocating profile allocated nodes and updating profile_nodes count")
        try:
            if -1 in (getattr(self, 'NUM_NODES', {})).values() and not cbs:
                node_mgr = nodemanager_adaptor if self.nodemanager_service_can_be_used else node_pool_mgr
                node_mgr.deallocate_nodes(self)
                self.num_nodes = len(profile_nodes)  # NOSONAR
                self.persist()
        except Exception as e:
            self.add_error_as_exception(e)
