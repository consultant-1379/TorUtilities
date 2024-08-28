from datetime import datetime, timedelta
from time import time, sleep

from enmutils.lib import log, cache
from enmutils.lib.exceptions import EnmApplicationError, EnvironError, TimeOutError
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib.enm_deployment import check_if_cluster_exists, check_if_ebs_tag_exists
from enmutils_int.lib.netex import search_and_save
from enmutils_int.lib.profile_flows.pm_flows.pmprofile import PmProfile
from enmutils_int.lib.pm_subscriptions import Subscription
from enmutils_int.lib import node_pool_mgr
from enmutils_int.lib.services import nodemanager_adaptor
from retrying import retry


class PmSubscriptionProfile(PmProfile):
    """
    PM subscription profile flows superclass
    """

    USER = None
    NETEX_QUERY = None

    def set_scheduled_times(self):
        """
        Sets SCHEDULED_TIMES

        """
        log.logger.debug("Setting scheduled times")

        current_timestamp_in_secs = int(time())
        current_timestamp = datetime.fromtimestamp(current_timestamp_in_secs)

        offset_from_start_of_rop_to_current_time_in_mins = (int(current_timestamp.strftime("%M")) %
                                                            self.ROP_DURATION_IN_MINS)
        offset_from_start_of_current_minute_in_secs = int(current_timestamp.strftime("%S"))

        start_of_rop_timestamp = (current_timestamp +
                                  timedelta(minutes=self.ROP_DURATION_IN_MINS) -
                                  timedelta(minutes=offset_from_start_of_rop_to_current_time_in_mins) -
                                  timedelta(seconds=offset_from_start_of_current_minute_in_secs))

        activation_time = (start_of_rop_timestamp +
                           timedelta(minutes=self.OFFSET_FROM_START_OF_ROP_TO_ACTIVATION_TIME_IN_MINS))

        enable_times = [activation_time + timedelta(hours=hour) for hour in
                        xrange(0, 23, self.ACTIVITY_FREQUENCY_HOURS)]

        disable_times = [activation_time + timedelta(hours=hour + self.ACTIVITY_DURATION_HOURS)
                         for hour in xrange(0, 23, self.ACTIVITY_FREQUENCY_HOURS)]

        scheduled_times = [val for pair in zip(enable_times, disable_times) for val in pair]
        setattr(self, 'SCHEDULED_TIMES', scheduled_times)
        log.logger.debug("Setting scheduled times complete: {0}"
                         .format(["{0}:{1}".format(_.strftime("%H"), _.strftime("%M")) for _ in scheduled_times]))

    def is_cluster_configured(self, cluster_name):
        """
        Check whether a Cluster/EBS Tag is present on the system.

        :param cluster_name: Name of the cluster
        :type cluster_name: str

        :return: Whether the given cluster is present.
        :rtype: Boolean
        """
        if cache.is_host_physical_deployment():
            cluster_exists = check_if_cluster_exists(cluster_name)
            if not cluster_exists:
                log.logger.debug("{0} Cluster not found in the deployment".format(cluster_name))
            return cluster_exists
        elif cache.is_enm_on_cloud_native():
            ebs_tag_exists = check_if_ebs_tag_exists(cluster_name)
            if not ebs_tag_exists:
                log.logger.debug("{0} Tag not found in the deployment".format(cluster_name))
            return ebs_tag_exists
        else:
            # Clusters currently not implemented in vENM, so we simply return False
            log.logger.debug("Deployment is vENM, so skipping the cluster check as they are not yet available "
                             "in this environment")
            return False

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

    def set_search_criteria(self):
        """
        Set search criteria

        If not in the system yet, save the criteria search.
        The node type query filter relies on the NUM_NODES dictionary profile attribute.

        :return List. The list contains a dictionary with the criteria search name and the netex query.
        """
        log.logger.debug("Setting the search criteria")
        nodes = self.all_nodes_in_workload_pool(node_attributes=["node_id", "poid", "primary_type", "node_version"])
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

    def set_subscription_description(self):
        """
        Define the subscription description using some of the profile attributes.

        :return String. The subscription description.
        """
        cbs_text = "cbs_" if hasattr(self, 'CBS') and self.CBS else ""
        subscription_description = "{0}_{1}load_profile".format(self.NAME, cbs_text)

        return subscription_description

    @retry(retry_on_exception=lambda e: isinstance(e, TimeOutError), wait_fixed=60, stop_max_attempt_number=3)
    def check_subscription_state(self, system_subscription, pattern=None):
        """
        Check if the provided system subscription exists and is active in the system
        with an interval defined by the profile SCHEDULE_SLEEP attribute.
        If the system subscription is not active, try to activate it.

        :param system_subscription: A system defined subscription object.
        :type system_subscription: enmutils_int.lib.pm_subscriptions.Subscription
        :param pattern: Pattern used to match System Defined subscriptions
        :type pattern: str
        :raises EnmApplicationError: if unexpected admin state is reported by ENM
        """

        while self.keep_running():
            log.logger.debug("Fetching subscription data for '{0}' from ENM".format(system_subscription.name))
            system_subscription_state = system_subscription.get_subscription()['administrationState']
            log.logger.debug("The value of 'administrationState' for subscription '{0}' is: {1}"
                             .format(system_subscription.name, system_subscription_state))

            if system_subscription_state == 'ACTIVE':
                log.logger.debug("The subscription '{0}' is ACTIVE as expected.".format(system_subscription.name))
                break

            elif system_subscription_state in ['ACTIVATING', 'DEACTIVATING', 'UPDATING']:
                self.add_error_as_exception(
                    EnvironError("The subscription '{0}' is in {1} state! It should be ACTIVE."
                                 .format(system_subscription.name, system_subscription_state)))
                log.logger.debug('Profile will check the system subscription in {} minutes from now.'
                                 .format(300 / 60))
                sleep(300)

            elif system_subscription_state == 'INACTIVE':
                if pattern in ["CCTR", "CTUM", "Continuous Cell Trace NRAN"]:
                    log.logger.debug("Subscription with name pattern '{0}' (i.e. {1}) is INACTIVE "
                                     "(i.e. expected default admin state)".format(pattern, system_subscription.name))

                else:
                    self.add_error_as_exception(
                        EnvironError("Subscription '{0}' is INACTIVE. "
                                     "Profile expects that the subscription is ACTIVE and will now try to activate it"
                                     .format(system_subscription.name)))

                log.logger.debug("The subscription '{0}' is being activated now.".format(system_subscription.name))
                system_subscription.activate()

                if pattern in ["CCTR", "CTUM", "Continuous Cell Trace NRAN"]:
                    log.logger.debug("Adding instruction to teardown_list to deactivate subscription '{0}' so that "
                                     "subscription is reverted to default admin state when profile is stopped."
                                     .format(system_subscription.name))
                    self.teardown_list.append(picklable_boundmethod(system_subscription.deactivate))
                break

            else:
                raise EnmApplicationError("Subscription '{0}' is in unexpected admin state: {1}"
                                          .format(system_subscription.name, system_subscription_state))

    def check_system_subscription_activation(self, system_subscription, pattern=None):
        """
        Get subscription by name and check its status

        :param system_subscription: A system defined subscription object.
        :type system_subscription: enmutils_int.lib.pm_subscriptions.Subscription
        :param pattern: Pattern used to match System Defined subscriptions
        :type pattern: str

        """

        log.logger.debug('The profile will check if the system subscription {0} exists and is active'
                         .format(system_subscription.name))
        try:
            system_subscription.get_by_name(system_subscription.name, self.USER)
            subscription_exists = True
        except (ValueError, EnmApplicationError):
            subscription_exists = False
            self.add_error_as_exception(EnmApplicationError("System Defined subscription '{0}' does not exist "
                                                            "on ENM - check PIB parameter/PMIC logs"
                                                            .format(system_subscription.name)))
        if subscription_exists:
            self.check_subscription_state(system_subscription, pattern)

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

    def get_subscription_file_generation_action_enable_or_disable_command(self, next_run_time, scheduled_times):
        """
        It returns next subscription file_generation_action command
        :param next_run_time: datetime for next iteration
        :type next_run_time: datetime
        :param scheduled_times: List of scheduled times
        :type scheduled_times: list
        :return: sub_action Enable, Disable
        :rtype: string
        """
        next_run_time = next_run_time.replace(microsecond=0)
        sub_action = "Disable"
        if next_run_time in [scheduled_time.replace(microsecond=0) for scheduled_time in scheduled_times if
                             scheduled_times.index(scheduled_time) % 2 == 0]:
            sub_action = "Enable"
        else:
            sub_action = "Disable"
        return sub_action

    def get_profile_nodes(self, node_attributes=None, cbs=None):
        """
        Get Nodes for profile
        :param node_attributes: List of Node attributes
        :type node_attributes: list
        :param cbs: CBS flag True, False
        :type cbs: bool
        :return: List of Node objects
        :rtype: list
        :raises EnmApplicationError: if no nodes found
        """
        node_attributes = node_attributes if node_attributes else ["node_id", "poid", "primary_type"]

        if self.NAME in ['PM_95', 'PM_96']:
            nodes_list = self.all_nodes_in_workload_pool(node_attributes=node_attributes)
            node_ids = [node.node_id for node in nodes_list]
            actual_node_count = (self.NUM_NODES.values()[0]
                                 if hasattr(self, 'NUM_NODES') and len(self.NUM_NODES.values()) else 0)
            profile_nodes = [node for node in nodes_list if node.node_id in sorted(node_ids)[:actual_node_count]]
        elif self.NAME in ['PM_102', 'PM_103', 'PM_104']:
            profile_nodes = self.get_nodes_list_by_attribute(node_attributes=node_attributes)
        elif hasattr(self, 'NODE_FILTER'):
            profile_nodes = self.get_all_nodes_in_workload_pool_based_on_node_filter()
        else:
            num_nodes = getattr(self, 'NUM_NODES', {})
            profile_nodes = (self.all_nodes_in_workload_pool(node_attributes=node_attributes)
                             if num_nodes and -1 in num_nodes.values() else
                             self.get_nodes_list_by_attribute(node_attributes=node_attributes))
        if not profile_nodes:
            raise EnmApplicationError('No nodes available for {0} profile'.format(self.NAME))
        log.logger.debug("Number of nodes to be used by the profile: {0}".format(len(profile_nodes)))
        self.deallocate_and_update_nodes_count_for_profile(profile_nodes, cbs)

        return profile_nodes

    def check_and_pick_cran_nodes(self, profile_nodes):
        """
        Deprecated in 24.09 and to be deleted in 25.04  ENMRTD-25460
        """

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
