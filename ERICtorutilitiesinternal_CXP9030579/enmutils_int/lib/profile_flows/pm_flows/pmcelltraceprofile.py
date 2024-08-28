from enmutils.lib import log
from enmutils_int.lib.pm_subscriptions import CelltraceSubscription, Subscription
from enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile import PmSubscriptionProfile


class PmCelltraceProfile(PmSubscriptionProfile):

    def create_celltrace_subscription(self):
        """
        Create and activate a celltrace subscription on ENM using the profile attributes.
        """
        subscription = self.create_celltrace_subscription_object()
        subscription.create()
        self.delete_nodes_from_netex_attribute()
        self.set_teardown(CelltraceSubscription, subscription.name, subscription.id, subscription.poll_scanners,
                          node_types=subscription.node_types)
        self.check_all_nodes_added_to_subscription(subscription)
        subscription.activate()

    def create_celltrace_subscription_object(self):
        """
        Create a celltrace subscription object
        """
        cbs, criteria = self.set_values_from_cbs()
        node_types = self.NUM_NODES.keys()
        subscription_name = self.identifier
        profile_nodes = self.get_profile_nodes(cbs=cbs)
        poll_scanners = getattr(self, "POLL_SCANNERS", False)
        subscription = CelltraceSubscription(
            name=subscription_name,
            cbs=cbs,
            description=self.set_subscription_description(),
            user=self.USER,
            poll_scanners=poll_scanners,
            nodes=getattr(self, 'nodes_from_netex', profile_nodes),
            rop_enum=getattr(self, 'ROP_STR', 'FIFTEEN_MIN'),
            num_counters=getattr(self, 'NUM_COUNTERS', None),
            mo_class_counters_excluded=getattr(self, 'MO_CLASS_COUNTERS_EXCLUDED', None),
            criteria_specification=criteria,
            cell_trace_category=getattr(self, 'CELL_TRACE_CATEGORY', None),
            event_filter=getattr(self, 'EVENT_FILTER', None),
            definer=getattr(self, "DEFINER", None),
            node_types=node_types)
        return subscription

    def check_celltrace_system_subscription(self, pattern, user):
        """
        PM profiles calling this:
        04

        Description:
        Retrieve the celltrace system subscription under test and check whether it is correct.

        :param pattern: Pattern that identifies the type of system defined subscription
        :type pattern: str
        :param user: User instance
        :type user: enmutils.lib.enm_user_2.User
        """
        log.logger.debug("Checking that System Defined Subscription exists")
        system_subscription_name = Subscription.get_system_subscription_name_by_pattern(pattern, user)

        system_subscription = CelltraceSubscription(name=system_subscription_name, user=user,
                                                    poll_scanners=self.POLL_SCANNERS if hasattr(
                                                        self, 'POLL_SCANNERS') else False)
        self.check_system_subscription_activation(system_subscription, pattern)

    def execute_flow(self, **kwargs):
        """
        Description:
        Call the superclass flow. Keyword arguments forwarded.
        If a subscription name is set for the profile, it's a system subscription that should already exist on the system.
        Otherwise, it's an user defined celltrace subscription that needs to be created by the profile.
        """
        try:
            super(PmCelltraceProfile, self).execute_flow(**kwargs)
            self.state = 'RUNNING'
            if hasattr(self, 'SYS_DEF_SUB_PATTERN'):
                # System defined subscription
                self.check_celltrace_system_subscription(self.SYS_DEF_SUB_PATTERN, user=self.USER)
            else:
                # User defined subscription
                self.create_celltrace_subscription()
        except Exception as e:
            self.delete_nodes_from_netex_attribute()
            self.add_error_as_exception(e)
