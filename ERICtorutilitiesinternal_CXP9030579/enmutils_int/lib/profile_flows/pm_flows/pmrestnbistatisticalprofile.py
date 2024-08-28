import time
from enmutils.lib import log, multitasking
from enmutils.lib.thread_queue import ThreadQueue
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.pm_rest_nbi_subscriptions import StatisticalSubscription
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.profile_flows.pm_flows.pmrestnbisubscriptionprofile import PmSubscriptionProfile


class PmStatisticalProfile(PmSubscriptionProfile, GenericFlow):
    OFFSET = 0
    THREAD_TIMEOUT = 60 * 60

    def create_statistical_subscription(self, sub_id, nodes):
        """
        Description:
        Create statistical subscription using the profile attributes.
        :param sub_id: subscription id
        :type sub_id: str
        :param nodes: nodeslist
        :type nodes: list

        :return: Subscription Object
        :rtype: StatisticalSubscription
        """
        subscription = self.create_statistical_subscription_object(sub_id, nodes)
        self.delete_nodes_from_netex_attribute()
        log.logger.debug("Subscription Created: {0}".format(subscription.name))
        return subscription

    def create_rest_nbi_subscriptions(self):
        """
        Create multiple PM REST NBI Statistical subscriptions

        :return: List of subscriptions created
        :rtype: list
        """
        log.logger.debug("Creating set of PM_REST_NBI subscriptions")
        subscriptions = []
        failed_subscriptions = 0
        selected_nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "poid", "primary_type"])
        equal_nodes = len(selected_nodes) // self.SUBSCRIPTION_COUNT
        remaining_nodes = len(selected_nodes) % self.SUBSCRIPTION_COUNT
        log.logger.debug("Profile required {0} nodes to create each subscription".format(equal_nodes))

        node_counter = 0
        for sub_id in xrange(self.SUBSCRIPTION_COUNT):
            if sub_id < remaining_nodes:
                nodes_for_subscription = selected_nodes[node_counter: node_counter + equal_nodes + 1]
                node_counter += (equal_nodes + 1)
            else:
                nodes_for_subscription = selected_nodes[node_counter: node_counter + equal_nodes]
                node_counter += equal_nodes
            log.logger.debug("Profile required {0} nodes to create subscription".format(len(nodes_for_subscription)))

            try:
                subscriptions.append(self.create_statistical_subscription(str(sub_id), nodes_for_subscription))
            except Exception as e:
                log.logger.debug("Error encountered during subscription creation: {0}".format(e))
                failed_subscriptions += 1

        if failed_subscriptions:
            self.add_error_as_exception(EnmApplicationError("Unable to create {0} PM REST NBI Statistical subscription(s)"
                                                            .format(failed_subscriptions)))

        log.logger.debug("Creating set of PM REST NBI Statistical subscriptions complete")
        log.logger.debug("subscriptions created {0}".format(subscriptions))
        return subscriptions

    def create_statistical_subscription_object(self, sub_id, nodes):
        """
        Create Statistical Subscription object based on certain prerequisites
        :param sub_id: subscription id
        :type sub_id: str
        :param nodes: nodeslist
        :type nodes: list

        :return: Subscription Object
        :rtype: StatisticalSubscription
        """
        subscription_name = self.identifier + sub_id
        log.logger.debug("Attempting to create subscription: {0}".format(subscription_name))
        node_types = self.NUM_NODES.keys()
        cbs, criteria = self.set_values_from_cbs()
        subscription_description = self.set_subscription_description()

        poll_scanners = getattr(self, "POLL_SCANNERS", False)

        subscription = StatisticalSubscription(
            name=subscription_name,
            cbs=cbs,
            description=subscription_description,
            user=self.USER,
            poll_scanners=poll_scanners,
            nodes=getattr(self, 'nodes_from_netex', nodes),
            rop_enum=getattr(self, 'ROP_STR', 'FIFTEEN_MIN'),
            timeout=getattr(self, 'WAIT_TIME', 15 * 60),
            num_counters=getattr(self, 'NUM_COUNTERS', None),
            mo_class_counters_excluded=getattr(self, 'MO_CLASS_COUNTERS_EXCLUDED', None),
            criteria_specification=criteria,
            technology_domain=getattr(self, "TECHNOLOGY_DOMAIN", None),
            mo_class_counters_included=getattr(self, "MO_CLASS_COUNTERS_INCLUDED", None),
            mo_class_sub_counters_included=getattr(self, "MO_CLASS_SUB_COUNTERS_INCLUDED", None),
            reserved_counters=getattr(self, "RESERVED_COUNTERS", None),
            definer=getattr(self, "DEFINER", None),
            node_types=node_types)
        return subscription

    def execute_flow(self, **kwargs):
        """
        Description:
        Call the superclass flow. Keyword arguments forwarded.
        If a subscription name is set for the profile, it's a system subscription that should already exist on the
        system. Otherwise, it's an user defined statistical subscription that needs to be created by the profile.
        """
        try:
            self.state = 'RUNNING'
            super(PmStatisticalProfile, self).execute_flow(**kwargs)
            subscriptions = self.create_rest_nbi_subscriptions()
            sub_operations = kwargs.get("operations")
        except Exception as e:
            self.add_error_as_exception(e)
        else:
            while self.keep_running():
                self.sleep_until_time()
                self.pm_rest_nbi_create_sub_operations(subscriptions, sub_operations)
                if "PM_REST_NBI_01" in self.NAME:
                    log.logger.debug("Sleeping for {0} seconds until next iteration".format(self.SCHEDULE_SLEEP))
                    self.state = 'SLEEPING'
                    time.sleep(self.SCHEDULE_SLEEP)
                    self.state = 'RUNNING'
                elif "PM_REST_NBI_02" in self.NAME:
                    log.logger.debug("Sleeping for {0} seconds until next iteration".format(self.WAIT_TIME))
                    time.sleep(self.WAIT_TIME)
                self.pm_rest_nbi_delete_sub_operations(subscriptions, sub_operations)

    def pm_rest_nbi_create_sub_operations(self, subscriptions, sub_operations):
        """
        Create Statistical Subscription
        :param subscriptions: subscriptions
        :type subscriptions: list
        :param sub_operations: operations type
        :type sub_operations: list
        """
        try:
            if "create" in sub_operations:
                multitasking.create_single_process_and_execute_task(
                    toggle_subscription_action_on_nodes, args=(self, 'create', subscriptions), fetch_result=True,
                    timeout=self.THREAD_TIMEOUT)
            if "activate" in sub_operations:
                multitasking.create_single_process_and_execute_task(
                    toggle_subscription_action_on_nodes, args=(self, 'activate', subscriptions), fetch_result=True,
                    timeout=self.THREAD_TIMEOUT)
        except Exception as e:
            self.add_error_as_exception(e)

    def pm_rest_nbi_delete_sub_operations(self, subscriptions, sub_operations):
        """
        Delete Statistical Subscription
        :param subscriptions: subscriptions
        :type subscriptions: list
        :param sub_operations: operations type
        :type sub_operations: list
        """
        try:
            if "deactivate" in sub_operations:
                multitasking.create_single_process_and_execute_task(
                    toggle_subscription_action_on_nodes, args=(self, 'deactivate', subscriptions), fetch_result=True,
                    timeout=self.THREAD_TIMEOUT)
            if "delete" in sub_operations:
                multitasking.create_single_process_and_execute_task(
                    toggle_subscription_action_on_nodes, args=(self, 'delete', subscriptions), fetch_result=True,
                    timeout=self.THREAD_TIMEOUT)
        except Exception as e:
            self.add_error_as_exception(e)


def toggle_subscription_action_on_node(subscription, file_generation_action, profile):
    """
    Toggle file generation on node (Disable -> Enable etc)

    :param subscription: subscription object
    :type subscription: enmutils_int.lib.pm_rest_nbi_subscriptions.StatisticalSubscription
    :param file_generation_action: Action to perform on Node (Enable/Disable)
    :type file_generation_action: str
    :param profile: Profile object
    :type profile: `PmBscRecordingsProfile`
    """

    if file_generation_action == 'create':
        subscription.create()
        profile.set_teardown(StatisticalSubscription, subscription.name, subscription.id, subscription.poll_scanners,
                             node_types=subscription.node_types)
    elif file_generation_action == 'activate':
        subscription.activate()
    elif file_generation_action == 'deactivate':
        subscription.deactivate()
    elif file_generation_action == 'delete':
        subscription.delete()


def toggle_subscription_action_on_nodes(profile, file_generation_action, subscriptions):
    """
    Toggle file generation on nodes (Disable -> Enable etc)
    :param file_generation_action: Action to perform on Nodes (Enable/Disable)
    :type file_generation_action: str
    :param subscriptions: list of PmStatisticalProfile objects
    :type subscriptions: list
    :param profile: Profile object
    :type profile: `PmBscRecordingsProfile`
    """
    tq = ThreadQueue(subscriptions, num_workers=len(subscriptions),
                     func_ref=toggle_subscription_action_on_node,
                     args=[file_generation_action, profile],
                     task_wait_timeout=profile.THREAD_TIMEOUT)
    tq.execute()
    profile.show_errored_threads(tq, len(subscriptions), EnmApplicationError)
