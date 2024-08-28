import time
from enmutils.lib import log
from enmutils.lib.exceptions import EnvironWarning
from enmutils_int.lib import enm_deployment
from enmutils_int.lib.pm_subscriptions import RPMOSubscription
from enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile import PmSubscriptionProfile


class PmRPMOSubscriptionProfile(PmSubscriptionProfile):
    sub_id = 0
    use_case_index = 0
    subscriptions = {"usecase1": [], "usecase2": []}
    STREAMING_CLUSTER_ID = "eba_EBA_vip_ipaddress"
    STR_CLUSTER_NOT_EXISTS_MESSAGE = (
        "This profile requires an Events (STREAMING) Cluster configured in this ENM deployment"
        "in order to create an 'RPMO Subscription' in PMIC."
        "Given that an STREAMING Cluster is NOT currently configured, this profile is not "
        "applicable to this deployment.")

    def create_rpmo_subscription(self, sub_id, subscription_with_nodes):
        """
        PM profiles using this:
        PM_80

        Create and activate a RPMO subscription using the profile attributes.

        :param sub_id: subscription count
        :type sub_id: int
        :param subscription_with_nodes: subscription nodes
        :type subscription_with_nodes: list
        """
        subscription_name = "{0}_{1}".format(self.identifier, sub_id)
        log.logger.debug('RPMO Subscription Name: {}'.format(subscription_name))
        subscription = RPMOSubscription(name=subscription_name,
                                        description=self.set_subscription_description(),
                                        user=self.USER, nodes=subscription_with_nodes)
        log.logger.debug('RPMO Subscription Creating')

        subscription.create()
        log.logger.debug('RPMO Subscription Created')

        self.set_teardown(RPMOSubscription, subscription_name, subscription.id)
        log.logger.debug('Check All Nodes Added To Subscription')

        self.check_all_nodes_added_to_subscription(subscription)
        self.subscriptions["usecase{0}".format(self.use_case_index + 1)].append(subscription)
        log.logger.debug("Subscriptions : {0}".format(self.subscriptions))

    def create_rpmo_subscriptions_based_on_use_cases(self):
        """
        Create rpmo subscriptions based on use case

        """
        use_case_details = self.USE_CASES[self.use_case_index]
        num_nodes_in_subscription = use_case_details['Nodes']
        offset_nodes = 0
        nodes_list = self.get_profile_nodes()

        log.logger.debug('Use-Case{0}: {1} subscription(s) with {2} BSC nodes running for 72 hrs'
                         .format(self.use_case_index + 1, use_case_details['Subscriptions'], num_nodes_in_subscription))
        for subscription_number in range(use_case_details['Subscriptions']):
            log.logger.debug("Creating subscription {0}".format(subscription_number + 1))
            remaining_nodes = len(nodes_list) - offset_nodes
            if remaining_nodes:
                nodes = nodes_list[offset_nodes:offset_nodes + num_nodes_in_subscription]
                log.logger.debug('Creating and Activating Subscription with {0} BSC nodes running for 72 hrs'
                                 .format(len(nodes)))
                self.create_rpmo_subscription(self.sub_id, nodes)
                offset_nodes += (num_nodes_in_subscription if remaining_nodes >= num_nodes_in_subscription
                                 else remaining_nodes)
                self.sub_id += 1
            else:
                log.logger.debug("Subscription {0} is not created on ENM as no nodes are left and Remaining "
                                 "subscriptions creation is also skipped".format(subscription_number + 1))
                break

        self.use_case_index = 1 if self.use_case_index == 0 else 0

    def deactivate_and_activate_rpmo_subscription(self):
        """
        deactivate rpmo subscriptions based on use case
         and wait for 2 minutes after activating another rpmo subscription.

        """
        for subscription in self.subscriptions["usecase{0}".format(self.use_case_index)]:
            log.logger.debug('Deactivating RPMO subscription')
            subscription.deactivate()
            log.logger.debug('Deactivated RPMO subscription')

        log.logger.debug('Profile will wait for 2 mins post the file collection'
                         ' time and then only deactivate the subscriptions.')
        self.use_case_index = 1 if self.use_case_index == 2 else 2
        time.sleep(120)
        self.activate_rpmo_subscription()

    def activate_rpmo_subscription(self):
        """
        activating rpmo subscriptions based on use case

        """
        for subscription in self.subscriptions["usecase{0}".format(self.use_case_index)]:
            log.logger.debug('Activating RPMO subscription')
            subscription.activate()
            log.logger.debug('Activated RPMO subscription')

    def main_rpmo_flow(self):
        """
        Main RPMO subscription flow

        """
        try:
            self.state = 'RUNNING'
            super(PmRPMOSubscriptionProfile, self).execute_flow()
            for _ in range(len(self.USE_CASES)):
                self.create_rpmo_subscriptions_based_on_use_cases()
            self.use_case_index = 1
            log.logger.debug('usecase{0} RPMO Subscription Activating'.format(self.use_case_index))
            subscription = self.subscriptions["usecase{0}".format(self.use_case_index)][0]
            subscription.activate()
            log.logger.debug('usecase{0} RPMO Subscription Activated'.format(self.use_case_index))
        except Exception as e:
            self.add_error_as_exception(e)
        else:
            while self.keep_running():
                self.sleep()
                try:
                    self.deactivate_and_activate_rpmo_subscription()
                except Exception as e:
                    self.add_error_as_exception(e)

    def execute_flow(self, **kwargs):
        """
        Execute flow to create RPMO subscription
        """
        try:
            str_cluster_exists = enm_deployment.get_values_from_global_properties(self.STREAMING_CLUSTER_ID)
            log.logger.debug("STREAMING Cluster configured in global properties: {0}".format(str_cluster_exists))
        except Exception as e:
            self.add_error_as_exception(e)
        else:
            if str_cluster_exists:
                self.main_rpmo_flow()
            else:
                self.add_error_as_exception(EnvironWarning(self.STR_CLUSTER_NOT_EXISTS_MESSAGE))
