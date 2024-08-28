from enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile import PmSubscriptionProfile
from enmutils_int.lib.pm_subscriptions import UETRSubscription


class PmUETRProfile(PmSubscriptionProfile):

    def create_uetr_subscription(self):
        """
        Create and activate a uetr subscription on ENM using the profile attributes.
        """
        subscription = self.create_uetr_subscription_object()
        subscription.create()
        self.set_teardown(UETRSubscription, subscription.name, subscription.id, subscription.poll_scanners)
        self.check_all_nodes_added_to_subscription(subscription)
        subscription.activate()

    def create_uetr_subscription_object(self):
        """
        Create a uetr subscription object
        :return: UETRSubscription object
        :rtype: UETRSubscription
        """
        subscription_name = self.identifier
        poll_scanners = getattr(self, "POLL_SCANNERS", False)
        profile_nodes = self.get_profile_nodes()
        subscription = UETRSubscription(
            name=subscription_name,
            description=self.set_subscription_description(),
            user=self.USER,
            poll_scanners=poll_scanners,
            nodes=profile_nodes,
            imsi=getattr(self, 'IMSI', [{"type": "IMSI", "value": "123546"}]),
            num_events=getattr(self, 'NUM_EVENTS', 3))
        return subscription

    def execute_flow(self, **kwargs):
        """
        PM profiles using this:
        47

        Description:
        Call the superclass flow. Keyword arguments forwarded.
        Create an user defined uetr subscription.

        :return Void
        """
        try:
            super(PmUETRProfile, self).execute_flow()
            self.state = 'RUNNING'
            # User defined subscription
            self.create_uetr_subscription()
        except Exception as e:
            self.add_error_as_exception(e)
