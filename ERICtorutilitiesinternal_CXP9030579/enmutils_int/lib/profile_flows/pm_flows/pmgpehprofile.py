from enmutils_int.lib.pm_subscriptions import GpehSubscription
from enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile import PmSubscriptionProfile


class PmGpehProfile(PmSubscriptionProfile):

    def create_gpeh_subscription(self):
        """
        Create and activate a gpeh subscription using the profile attributes.
        """
        subscription = self.create_gpeh_subscription_object()
        subscription.create()
        self.delete_nodes_from_netex_attribute()
        self.set_teardown(GpehSubscription, subscription.name, subscription.id, subscription.poll_scanners)
        self.check_all_nodes_added_to_subscription(subscription)
        subscription.activate()

    def create_gpeh_subscription_object(self):
        """
        Create GPEH Subscription object
        :return: GpehSubscription object
        :rtype: GpehSubscription
        """
        cbs, criteria = self.set_values_from_cbs()

        subscription_name = self.identifier
        profile_nodes = self.get_profile_nodes(cbs=cbs)
        subscription_description = self.set_subscription_description()

        poll_scanners = getattr(self, "POLL_SCANNERS", False)
        subscription = GpehSubscription(
            name=subscription_name,
            cbs=cbs,
            description=subscription_description,
            user=self.USER,
            poll_scanners=poll_scanners,
            nodes=getattr(self, 'nodes_from_netex', profile_nodes),
            rop_enum=getattr(self, 'ROP_STR', 'FIFTEEN_MIN'),
            num_events=getattr(self, 'NUM_EVENTS', 3),
            criteria_specification=criteria)
        return subscription

    def execute_flow(self, **kwargs):
        """
        Description:
        Call the superclass flow. Keyword arguments forwarded.
        Create an user defined gpeh subscription.
        """
        try:
            super(PmGpehProfile, self).execute_flow(**kwargs)
            self.state = 'RUNNING'
            # User defined subscription
            self.create_gpeh_subscription()
        except Exception as e:
            self.delete_nodes_from_netex_attribute()
            self.add_error_as_exception(e)
