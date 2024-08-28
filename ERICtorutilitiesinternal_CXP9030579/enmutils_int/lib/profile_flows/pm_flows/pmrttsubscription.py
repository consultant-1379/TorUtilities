import time
from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError, EnvironWarning
from enmutils_int.lib import enm_deployment
from enmutils_int.lib.pm_subscriptions import RTTSubscription
from enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile import PmSubscriptionProfile


class PmRTTSubscription(PmSubscriptionProfile):
    STREAMING_CLUSTER_VIP_IP = "eba_EBA_vip_ipaddress"
    STR_CLUSTER_NOT_EXISTS_MESSAGE = ("This profile requires an Events (STREAMING)"
                                      " Cluster configured in this ENM deployment"
                                      " in order to create an 'RTT Subscription' in PMIC."
                                      " Given that an STREAMING Cluster is NOT currently configured,"
                                      " this profile is not applicable to this deployment.")

    def create_rtt_subscription(self):
        """
        Create rtt Subscription using the profile  attributes.
        :return: rttSubscription object
        :rtype: rttSubscription
        """
        subscription_name = "{0}".format(self.identifier)
        nodes_list = self.get_nodes_list_by_attribute(node_attributes=["node_id", "poid", "primary_type"])
        subscription = RTTSubscription(name=subscription_name,
                                       description=self.set_subscription_description(),
                                       user=self.USER, nodes=nodes_list)
        log.logger.debug("Create Subscription: {0}".format(subscription_name))
        subscription.create()
        log.logger.debug('RTT Subscription Created')
        self.set_teardown(RTTSubscription, subscription_name, subscription.id)
        log.logger.debug('Check All Nodes Added To Subscription')
        self.check_all_nodes_added_to_subscription(subscription)
        return subscription

    def main_rtt_flow(self):
        """
        Main RTT subscription flow

        """
        try:
            self.state = 'RUNNING'
            super(PmRTTSubscription, self).execute_flow()
            subscription = self.create_rtt_subscription()

            log.logger.debug('RTT Subscription Activating')
            subscription.activate()
            log.logger.debug('RTT Subscription Activated')

            while self.keep_running():
                self.sleep()
                try:
                    log.logger.debug("Fetching state of subscription")
                    profile_state = subscription.get_subscription()['administrationState']
                    log.logger.debug("State of subscription is currently {0}".format(profile_state))
                    if profile_state in ['ACTIVE', 'INACTIVE']:
                        if profile_state == 'ACTIVE':
                            log.logger.debug('deactivating RTT subscription')

                            subscription.deactivate()
                            log.logger.debug('deactivated RTT subscription')
                            log.logger.debug('Profile will wait for 2 mins post the file collection'
                                             ' time and then only activate the subscriptions.')
                            time.sleep(120)
                        log.logger.debug('activating RTT subscription')
                        subscription.activate()
                        log.logger.debug('activated RTT subscription')
                    else:
                        message = ("Unexpected subscription state {0}. Profile only expects either ACTIVE or "
                                   "INACTIVE states. This may indicate that an ENM problem exists and it should "
                                   "be investigated.".format(profile_state))
                        log.logger.debug(message)
                        raise EnmApplicationError(message)
                except Exception as e:
                    self.add_error_as_exception(e)
        except Exception as e:
            self.add_error_as_exception(e)

    def execute_flow(self, **kwargs):
        """
        Execute flow to create RTT subscription

        """
        try:
            str_cluster_exists = enm_deployment.get_values_from_global_properties(self.STREAMING_CLUSTER_VIP_IP)
            log.logger.debug("STREAMING Cluster configured in global properties: {0}".format(str_cluster_exists))
        except Exception as e:
            self.add_error_as_exception(e)
        else:
            if str_cluster_exists:
                self.main_rtt_flow()

            else:
                self.add_error_as_exception(EnvironWarning(self.STR_CLUSTER_NOT_EXISTS_MESSAGE))
