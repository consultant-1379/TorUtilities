from enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile import PmSubscriptionProfile
from enmutils_int.lib.nrm_default_configurations.basic_network import PM_20_NOTE
from enmutils_int.lib.pm_subscriptions import EBMSubscription
from enmutils.lib.exceptions import EnvironWarning
from enmutils.lib import log, cache


class PmEBMProfile(PmSubscriptionProfile):

    def create_ebm_subscription(self):
        """
        Create and activate an ebm subscription on ENM using the profile attributes.
        Generation of ebm Counter Files will NOT be enabled by this subscription.
        :return: EBMSubscription object
        :rtype: EBMSubscription
        """
        subscription = self.create_ebm_subscription_object()
        subscription.create()
        self.delete_nodes_from_netex_attribute()
        self.set_teardown(EBMSubscription, subscription.name, subscription.id, subscription.poll_scanners)
        self.check_all_nodes_added_to_subscription(subscription)
        log.logger.debug("EBM Subscription Created: {0}".format(subscription.name))
        return subscription

    def create_ebm_subscription_object(self):
        """
        Create EBM Subscription object
        :return: EBMSubscription object
        :rtype: EBMSubscription
        """
        subscription_name = "{}-EBM".format(self.identifier)
        log.logger.debug("Attempting to create EBM subscription: {0}".format(subscription_name))
        subscription_description = self.set_subscription_description()
        cbs, criteria = self.set_values_from_cbs()
        profile_nodes = self.get_profile_nodes(cbs=cbs)
        poll_scanners = getattr(self, "POLL_SCANNERS", False)
        subscription = EBMSubscription(
            name=subscription_name,
            num_events=self.NUM_EVENTS,
            cbs=cbs,
            description=subscription_description,
            user=self.USER,
            criteria_specification=criteria,
            poll_scanners=poll_scanners,
            nodes=getattr(self, 'nodes_from_netex', profile_nodes),
            rop_enum=self.ROP_STR,
            definer=getattr(self, "DEFINER", None))
        return subscription

    def execute_flow(self, **kwargs):
        """
        PM profiles using this:
        20

        Description:
        Call the superclass flow. Keyword arguments forwarded.
        If an Event Cluster is not implemented in the system, create user defined ebm subscription.

        :return Void
        """
        try:
            super(PmEBMProfile, self).execute_flow()
            self.state = 'RUNNING'
            cluster_name = "value_pack_ebs_m" if cache.is_enm_on_cloud_native() else "evt"
            if not self.is_cluster_configured(cluster_name):
                log.logger.debug("Creating EBM Subscription")
                subscription = self.create_ebm_subscription()
                log.logger.debug("Activating EBM Subscription")
                subscription.activate()
            else:
                raise EnvironWarning(PM_20_NOTE)
        except Exception as e:
            self.delete_nodes_from_netex_attribute()
            self.add_error_as_exception(e)
