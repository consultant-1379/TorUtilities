import re
from time import sleep

from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib.thread_queue import ThreadQueue
from enmutils_int.lib.pm_subscriptions import MtrSubscription
from enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile import PmSubscriptionProfile
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


def toggle_state_of_subscription(subscription, action):
    """
    Activate/Deactivate MTR subscription

    :param subscription: Subscription object
    :type subscription: `MtrSubscription`
    :param action: Activate/Deactivate action
    :type action: str
    """
    log.logger.debug("Toggling state of MTR subscription: {0}".format(subscription.name))

    subscription_index = int(subscription.name[-1])
    if 4 <= subscription_index <= 7:
        log.logger.debug("Sleeping for 10s before activation of {0}".format(subscription.name))
        sleep(10)
    if subscription_index >= 8:
        log.logger.debug("Sleeping for 20s before activation of {0}".format(subscription.name))
        sleep(20)

    if action == "activate":
        log.logger.debug("Activating Subscription: {0}".format(subscription.name))
        subscription.activate()
    else:
        log.logger.debug("Deactivating Subscription: {0}".format(subscription.name))
        subscription.deactivate()
    log.logger.debug("Toggling state of MTR subscriptions complete")


class PmMtrProfile(PmSubscriptionProfile, GenericFlow):
    SUBSCRIPTION_COUNT = 10
    IMSI_BASE_VALUE = 11111100

    THREAD_TIMEOUT = 20 * 60

    def create_mtr_subscription(self, sub_id, nodes):
        """
        Create an MTR Subscription using the profile  attributes.

        :param sub_id: Subscription identifier
        :type sub_id: int
        :param nodes: List of Node objects
        :type nodes: list
        :return: MtrSubscription object
        :rtype: MtrSubscription
        """

        subscription_name = "{0}_{1}".format(self.identifier, sub_id)
        subscription = MtrSubscription(**{"name": subscription_name,
                                          "description": self.set_subscription_description(),
                                          "user": self.USER,
                                          "nodes": nodes,
                                          "imsi_value": self.IMSI_BASE_VALUE + sub_id})

        log.logger.debug("Create Subscription: {0}".format(subscription.name))
        subscription.recording_reference = sub_id
        subscription.create()

        self.set_teardown(MtrSubscription, subscription_name, subscription.id)

        return subscription

    def create_mtr_subscriptions(self):
        """
        Create multiple MTR subscriptions

        :return: List of subscriptions created
        :rtype: list
        """
        log.logger.debug("Creating set of MTR subscriptions")
        subscriptions = []
        failed_subscriptions = 0
        nodes = self.get_profile_nodes()
        selected_nodes = self.check_whether_msc_nodes_connected_bsc_nodes_existed_in_workload_pool(nodes)

        nodes = selected_nodes[:self.TOTAL_REQUIRED_NODES]
        log.logger.debug("Profile required {0} nodes and took {1} nodes out of {2} nodes".format(
            self.TOTAL_REQUIRED_NODES, len(selected_nodes), len(nodes)))

        node_counter = 0
        for sub_id in xrange(self.SUBSCRIPTION_COUNT):
            if node_counter >= len(nodes):
                node_counter = 0
            nodes_for_subscription = nodes[node_counter: node_counter + self.NODES_PER_SUBSCRIPTION]
            node_counter += self.NODES_PER_SUBSCRIPTION

            try:
                subscriptions.append(self.create_mtr_subscription(sub_id, nodes_for_subscription))
            except Exception as e:
                log.logger.debug("Error encountered during subscription creation: {0}".format(e))
                failed_subscriptions += 1

        if failed_subscriptions:
            self.add_error_as_exception(EnmApplicationError("Unable to create {0} MTR subscription(s)"
                                                            .format(failed_subscriptions)))

        log.logger.debug("Creating set of MTR subscriptions complete")
        return subscriptions

    def toggle_state_of_subscriptions(self, subscriptions):
        """
        Activate/Deactivate MTR subscriptions
        :param subscriptions: List of subscription objects
        :type subscriptions: list
        """
        log.logger.debug("Toggling state of MTR subscriptions")
        action = "deactivate"
        previous_sub_action = action

        while self.keep_running():
            self.sleep_until_time()
            try:
                action = self.get_subscription_file_generation_action_enable_or_disable_command(
                    self.next_run_time, self.get_schedule_times())
                action = "activate" if action == "Enable" else "deactivate"
                if previous_sub_action != action:
                    self.activate_deactivate_mtr_subscriptions_with_threads(action, subscriptions)
                    previous_sub_action = action
            except Exception as e:
                self.add_error_as_exception(e)

    def activate_deactivate_mtr_subscriptions_with_threads(self, action, subscriptions):
        """
        Activate/Deactivate MTR subscriptions with threads
        :param action: activate or deactivate
        :type action: str
        :param subscriptions: List of subscription objects
        :type subscriptions: list
        """
        tq = ThreadQueue(subscriptions, num_workers=len(subscriptions), func_ref=toggle_state_of_subscription,
                         args=[action], task_wait_timeout=self.THREAD_TIMEOUT)
        tq.execute()
        self.show_errored_threads(tq, len(subscriptions), EnmApplicationError)

    def execute_flow(self, **kwargs):
        """
        Execute flow to create MTR subscription

        :return Void
        """
        try:
            self.state = 'RUNNING'
            super(PmMtrProfile, self).execute_flow(**kwargs)
            subscriptions = self.create_mtr_subscriptions()
        except Exception as e:
            self.add_error_as_exception(e)
        else:
            if subscriptions:
                self.toggle_state_of_subscriptions(subscriptions)
            else:
                self.add_error_as_exception(EnmApplicationError("No MTR subscriptions created"))

    def get_msc_node_connected_bsc_nodes(self, node_id):
        """
        Get MSC node connected bsd nodes id's

        :type node_id: str
        :param node_id: msc node id

        :return: List of bsc node id's
        :rtype: list
        """
        cmd = "cmedit get * NetworkElement.connectedMsc=='NetworkElement={msc_node_name}'"
        response = self.USER.enm_execute(cmd.format(msc_node_name=node_id))
        enm_output = response.get_output()
        match_pattern = '(^FDN\\s+:\\s+)(.*)'
        bsc_nodes = []
        if "instance(s)" in " ".join(enm_output):
            for line in enm_output:
                if re.search(match_pattern, line):
                    fdn = str(line.split()[-1])
                    bsc_node_id = fdn.split("NetworkElement=")[1]
                    bsc_nodes.append(bsc_node_id)
            log.logger.debug("{0} MSC node connected with {1} BSC nodes".format(node_id, bsc_nodes))
        else:
            log.logger.debug("Problem encountered while trying to perform ENM command '{0}' - {1}".format(cmd,
                                                                                                          enm_output))
        return bsc_nodes

    def check_whether_msc_nodes_connected_bsc_nodes_existed_in_workload_pool(self, profile_allocated_nodes):
        """
        MSC nodes which are being selected for PM_78 should have check -
        such that only MSC nodes with the corresponding BSC nodes are in the workload pool.

        :type profile_allocated_nodes: list
        :param profile_allocated_nodes: list of profile allocated msc nodes

        :return: List of MSC nodes (which msc nodes are connected BSC nodes are existed on workload pool)
        :rtype: list
        """
        # Fetching all nodes from workload pool
        nodes_list = self.all_nodes_in_workload_pool(node_attributes=["node_id", "poid", "primary_type"],
                                                     is_num_nodes_required=False)
        # fetching all node id's from nodes_list
        node_ids = [node.node_id for node in nodes_list]
        msc_nodes_with_bsc_nodes = []
        log.logger.debug("Fetching MSC nodes connected BSC nodes from workload pool")
        for node in profile_allocated_nodes:
            bsc_nodes = self.get_msc_node_connected_bsc_nodes(node.node_id)
            # checks the whether bsc nodes existed on workload pool or not.
            if bsc_nodes:
                count = 0
                for bsc_node in bsc_nodes:
                    if bsc_node in node_ids:
                        count += 1
                # checks the whether selected bsc nodes existed on workload pool or not.
                # connected msc nodes will deallocated from profile, when associated bsc nodes are not existed in pool.
                if len(bsc_nodes) == count:
                    msc_nodes_with_bsc_nodes.append(node.node_id)

        profile_allocated_msc_nodes = [node for node in profile_allocated_nodes if node.node_id in
                                       msc_nodes_with_bsc_nodes]
        unused_nodes = [node for node in profile_allocated_nodes if node.node_id not in msc_nodes_with_bsc_nodes]

        log.logger.debug("Deallocating the unused nodes from {0} profile".format(self.NAME))
        self.update_profile_persistence_nodes_list(unused_nodes)
        log.logger.debug("{0} MSC nodes found with connected BSC nodes in "
                         "workload pool".format(len(profile_allocated_msc_nodes)))

        return profile_allocated_msc_nodes
