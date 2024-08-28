from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.pm_subscriptions import CelltrafficSubscription, Subscription
from enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile import PmSubscriptionProfile


class PmCelltrafficProfile(PmSubscriptionProfile):

    def create_celltraffic_subscription(self):
        """
        Create and activate a celltraffic subscription on ENM using the profile attributes.
        """
        profile_nodes = self.get_profile_nodes()
        failed_subscriptions = 0
        log.logger.debug("Creating {0} CTR subscription(s)".format(self.NUM_OF_SUBSCRIPTIONS))
        for sub_id in range(self.NUM_OF_SUBSCRIPTIONS):
            subscription_name = "{0}_{1}".format(self.identifier, sub_id)
            try:
                subscription = self.create_celltraffic_subscription_object(profile_nodes, subscription_name)
                log.logger.debug("Create Subscription: {0}".format(subscription.name))
                subscription.create()
                self.set_teardown(CelltrafficSubscription, subscription.name, subscription.id, subscription.poll_scanners)
                self.check_all_nodes_added_to_subscription(subscription)
                subscription.activate()
            except Exception as e:
                log.logger.debug("Error encountered during {0} subscription creation/activation: {1}"
                                 "".format(subscription_name, e))
                failed_subscriptions += 1

        if failed_subscriptions:
            self.add_error_as_exception(EnmApplicationError("Unable to create/activate {0} CTR subscription(s)"
                                                            .format(failed_subscriptions)))
        log.logger.debug("{0} CTR subscription(s) are created/activated "
                         "successfully".format(self.NUM_OF_SUBSCRIPTIONS))

    def create_celltraffic_subscription_object(self, profile_nodes, subscription_name):
        """
        Create a celltraffic subscription
        :param profile_nodes: nodes on which the module is to be activated
        :type profile_nodes: list
        :param subscription_name: Name of the subscription.
        :type subscription_name: str

        :return: CelltrafficSubscription object
        :rtype: CelltrafficSubscription
        """
        poll_scanners = getattr(self, "POLL_SCANNERS", False)
        subscription = CelltrafficSubscription(
            name=subscription_name,
            description=self.set_subscription_description(),
            num_events=getattr(self, 'NUM_EVENTS', 3),
            user=self.USER,
            poll_scanners=poll_scanners,
            nodes=profile_nodes)
        return subscription

    def check_celltraffic_system_subscription(self, pattern, user):
        """
        PM profiles using this:
        29

        Description:
        Retrieve the celltraffic system subscription under test and check whether it is correct.

        :param pattern: Pattern that identifies the type of system defined subscription
        :type pattern: str
        :param user: User instance
        :type user: enmutils.lib.enm_user_2.User
        """
        log.logger.debug("Checking that System Defined Subscription exists")
        system_subscription_name = Subscription.get_system_subscription_name_by_pattern(pattern, user)

        system_subscription = CelltrafficSubscription(name=system_subscription_name, user=user,
                                                      poll_scanners=self.POLL_SCANNERS if hasattr(
                                                          self, 'POLL_SCANNERS') else False)
        self.check_system_subscription_activation(system_subscription)

    def execute_flow(self, **kwargs):
        """
        PM profiles using this:
        29

        Description:
        Call the superclass flow. Keyword arguments forwarded.
        If a subscription name is set for the profile, it's a system subscription that should already exist on the system.
        Otherwise, it's an user defined celltraffic subscription that needs to be created by the profile.

        :return Void
        """
        try:
            super(PmCelltrafficProfile, self).execute_flow()
            self.state = 'RUNNING'
            if hasattr(self, 'SYS_DEF_SUB_PATTERN'):
                # System defined subscription
                self.check_celltraffic_system_subscription(self.SYS_DEF_SUB_PATTERN, user=self.USER)
            else:
                # User defined subscription
                self.create_celltraffic_subscription()
        except Exception as e:
            self.add_error_as_exception(e)
