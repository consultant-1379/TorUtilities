import time
from functools import partial

from enmutils.lib import log
from enmutils.lib.exceptions import NetsimError
from enmutils.lib.persistence import picklable_boundmethod
from enmutils.lib.thread_queue import ThreadQueue
from enmutils_int.lib.pm_subscriptions import BscRecordingsSubscription
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile import PmSubscriptionProfile


def toggle_file_generation_on_node(node, file_generation_action, profile):
    """
    Toggle file generation on node (Disable -> Enable etc)

    :param node: Node object
    :type node: enmutils.lib.enm_node.Node
    :param file_generation_action: Action to perform on Node (Enable/Disable)
    :type file_generation_action: str
    :param profile: Profile object
    :type profile: `PmBscRecordingsProfile`
    :return: Boolean to indicate success of failure
    :rtype: bool
    """
    log.logger.debug("{0} PM file generation on node: {1}".format(file_generation_action, node.node_id))

    return toggle_file_generation_on_bsc_node(node, file_generation_action, profile)


def toggle_file_generation_on_bsc_node(node, file_generation_action, profile):
    """
    Toggle file generation on bsc node (Disable -> Enable etc)

    :param node: Node object
    :type node: enmutils.lib.enm_node.Node
    :param file_generation_action: Action to perform on Node (Enable/Disable)
    :type file_generation_action: str
    :param profile: Profile object
    :type profile: `PmBscRecordingsProfile`
    :return: Boolean to indicate success of failure
    :rtype: bool
    :raises NetsimError: if could not toggle file generation on node
    """
    success_count = 0
    for bsc_recording_type in profile.BSC_RECORDING_TYPES:
        if "Enable" in file_generation_action:
            enable_pmdata_cmd = "bscrecordings:enable,type={0};".format(bsc_recording_type)
            if profile.execute_netsim_command_on_netsim_node([node], enable_pmdata_cmd):
                success_count += 1
        else:
            disable_pmdata_cmd = "bscrecordings:disable,type={0};".format(bsc_recording_type)
            if profile.execute_netsim_command_on_netsim_node([node], disable_pmdata_cmd):
                success_count += 1

    if success_count == len(profile.BSC_RECORDING_TYPES):
        log.logger.debug("{0} PM file generation successfully completed on node: {1}"
                         .format(file_generation_action, node.node_id))

        return True
    raise NetsimError("{0} PM file generation on node {1} encountered problems"
                      .format(file_generation_action, node.node_id))


class PmBscRecordingsProfile(PmSubscriptionProfile, GenericFlow):
    BSC_RECORDING_TYPES = ["BAR", "RIR", "CTR", "CER", "MRR"]
    THREAD_TIMEOUT = 5 * 60

    def create_bsc_recording_subscription(self):
        """
        Create a BSC-Recording Subscription on ENM using the profile attributes.
        :return: BscRecordingsSubscription object
        :rtype: BscRecordingsSubscription
        """
        subscription = self.create_bsc_recording_subscription_object()
        subscription.create()

        self.set_teardown(BscRecordingsSubscription, subscription.name, subscription.id)
        log.logger.debug("Subscription created successfully")

        return subscription

    def create_bsc_recording_subscription_object(self):
        """
        Create a BSC-Recording Subscription object
        :return: BscRecordingsSubscription object
        :rtype: BscRecordingsSubscription
        """

        subscription_name = self.identifier
        profile_nodes = self.get_profile_nodes(node_attributes=["node_id", "poid", "primary_type",
                                                                "node_name", "netsim", "simulation"])
        subscription = BscRecordingsSubscription(**{"name": subscription_name,
                                                    "description": self.set_subscription_description(),
                                                    "user": self.USER,
                                                    "nodes": profile_nodes})
        return subscription

    def toggle_file_generation_on_nodes(self, file_generation_action, subscription):
        """
        Toggle file generation on nodes (Disable -> Enable etc)

        :param file_generation_action: Action to perform on Nodes (Enable/Disable)
        :type file_generation_action: str
        :param subscription: BSC Recordings Subscription object
        :type subscription: enmutils_int.lib.pm_subscriptions.BscRecordingsSubscription
        """
        log.logger.debug("{0} file generation on nodes being used in BSC Recordings subscription: {1}"
                         .format(file_generation_action, subscription.name))

        log.logger.debug("Starting threads for all {0} nodes".format(len(subscription.nodes)))
        tq = ThreadQueue(subscription.nodes, num_workers=len(subscription.nodes),
                         func_ref=toggle_file_generation_on_node,
                         args=[file_generation_action, self],
                         task_wait_timeout=self.THREAD_TIMEOUT)
        tq.execute()
        self.show_errored_threads(tq, len(subscription.nodes), NetsimError)

        log.logger.debug("{0} file generation on nodes being used in BSC Recordings subscription - complete"
                         .format(file_generation_action))

    def update_teardown_list(self, file_generation_action, subscription):
        """
        Update the Tear down list
        :param file_generation_action: Enable/Disable PM on Nodes
        :type file_generation_action: str
        :param subscription: PM Subscription
        :type subscription: BscRecordingsSubscription
        """
        log.logger.debug("Update Teardown list")

        if "Enable" in file_generation_action:
            self.teardown_list.append(partial(picklable_boundmethod(self.toggle_file_generation_on_nodes),
                                              "Disable", subscription))
        else:
            for item in self.teardown_list:
                if callable(item) and hasattr(item, "args") and file_generation_action in item.args:
                    log.logger.debug("Removing partial object from teardown list: {0}".format(item))
                    self.teardown_list.remove(item)

        log.logger.debug("Update Teardown list - complete")

    def execute_flow(self, **kwargs):
        """
        Execute flow to create BSC Recording subscription

        """
        try:
            self.state = 'RUNNING'
            super(PmBscRecordingsProfile, self).execute_flow(**kwargs)
            subscription = self.create_bsc_recording_subscription()
            file_generation_action = "Disable"
            previous_file_generation_action = file_generation_action
        except Exception as e:
            self.add_error_as_exception(e)

        else:
            while self.keep_running():
                self.sleep_until_time()
                try:
                    file_generation_action = self.get_subscription_file_generation_action_enable_or_disable_command(
                        self.next_run_time, self.get_schedule_times())
                    log.logger.debug("Sleeping for 5 seconds before activating or deactivating subscription")
                    time.sleep(5)
                    previous_file_generation_action = self.activate_deactivate_subscription_with_nodes(
                        file_generation_action, previous_file_generation_action, subscription)
                except Exception as e:
                    self.add_error_as_exception(e)

    def activate_deactivate_subscription_with_nodes(self, file_generation_action, previous_file_generation_action,
                                                    subscription):
        """
        This function activate or deactivate the subscription along with
        enable or disable file generation action on nodes.
        :param file_generation_action: Enable or Disable
        :type file_generation_action: str
        :param previous_file_generation_action: last file generation action either Enable or Disable
        :type previous_file_generation_action: str
        :param subscription: BSC Recordings Subscription object
        :type subscription: enmutils_int.lib.pm_subscriptions.BscRecordingsSubscription
        :return: previous_file_generation_action Enable, Disable
        :rtype: str
        """
        try:
            if previous_file_generation_action != file_generation_action:
                if file_generation_action == "Enable":
                    self.toggle_file_generation_on_nodes(file_generation_action, subscription)
                    subscription.activate()
                    previous_file_generation_action = file_generation_action
                else:
                    subscription.deactivate()
                    self.toggle_file_generation_on_nodes(file_generation_action, subscription)
                    previous_file_generation_action = file_generation_action
            self.update_teardown_list(file_generation_action, subscription)
            return previous_file_generation_action
        except Exception as e:
            self.add_error_as_exception(e)
