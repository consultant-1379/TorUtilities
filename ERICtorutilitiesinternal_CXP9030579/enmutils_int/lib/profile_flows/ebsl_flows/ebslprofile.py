from enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile import PmSubscriptionProfile
from enmutils_int.lib.pm_subscriptions import CelltraceSubscription
from enmutils.lib.exceptions import EnvironWarning
from enmutils.lib import log, cache


STREAM_01_SUBSCRIPTION_NAME = 'EBSL_STREAM_01_CellTrace_subscription'


class EBSLProfile(PmSubscriptionProfile):

    USER = None

    def create_celltrace_ebsl_subscription(self, subscription_name):
        """
        Create an CellTrace subscription with EBS flag enabled.

        :param subscription_name: Name of the subscription.
        :type subscription_name: str.

        :return Void.
        """
        cbs, criteria = self.set_values_from_cbs()
        poll_scanners = getattr(self, "POLL_SCANNERS", False)

        profile_nodes = self.get_all_nodes_in_workload_pool_based_on_node_filter()

        log.logger.debug("Number of nodes allocated to the profile {0}".format(len(profile_nodes)))
        subscription = CelltraceSubscription(name=subscription_name,
                                             description=self.set_subscription_description(),
                                             user=self.USER,
                                             poll_scanners=poll_scanners,
                                             nodes=profile_nodes,
                                             rop_enum=self.ROP_STR if hasattr(self, 'ROP_STR') else 'FIFTEEN_MIN',
                                             num_counters=self.NUM_COUNTERS if hasattr(self, 'NUM_COUNTERS') else None,
                                             num_events=self.NUM_EVENTS if hasattr(self, 'NUM_EVENTS') else 3,
                                             output_mode=self.OUTPUT_MODE if hasattr(self, 'OUTPUT_MODE') else 'FILE',
                                             ebs_enabled='true',
                                             cell_trace_category=getattr(self, 'CELL_TRACE_CATEGORY', None),
                                             event_filter=getattr(self, 'EVENT_FILTER', None),
                                             definer=getattr(self, "DEFINER", None),
                                             cbs=cbs,
                                             criteria_specification=criteria)
        subscription.create()
        self.set_teardown(CelltraceSubscription, subscription_name, subscription.id, poll_scanners)
        self.check_all_nodes_added_to_subscription(subscription)
        subscription.activate()

    def execute_flow(self, **kwargs):  # pylint: disable=arguments-differ
        """
        Overriding the superclass flow. EBSL profiles need to have their own flow.

        :type kwargs: dict
        :param kwargs: __builtin__ dictionary
        """
        self.NETEX_QUERY = kwargs.pop('netex_query', None)
        self.USER = self.create_users(1, roles=self.USER_ROLES, fail_fast=False, retry=True)[0]


class EBSL05Profile(EBSLProfile):

    def execute_flow(self, **kwargs):  # pylint: disable=arguments-differ
        """
        Main flow for EBSL_05

        :type kwargs: dict
        :param kwargs: __builtin__ dictionary
        """
        self.state = 'RUNNING'
        message = ("For {0} deployment, This profile requires an {1} configured in this ENM deployment But {1} is "
                   "NOT currently configured")
        try:
            super(EBSL05Profile, self).execute_flow(**kwargs)
            if cache.is_enm_on_cloud_native():
                cluster_name = "value_pack_ebs_ln"
                error_message = message.format("cENM", "value_pack_ebs_ln Tag")
            else:
                cluster_name = "evt"
                error_message = message.format("pENM" if cache.is_host_physical_deployment else "vENM",
                                               "Events (EVT) Cluster")

            if self.is_cluster_configured(cluster_name):
                subscription_name = self.identifier
                self.create_celltrace_ebsl_subscription(subscription_name)
            else:
                self.add_error_as_exception(EnvironWarning(error_message))
        except Exception as e:
            self.add_error_as_exception(e)


class EBSL06Profile(EBSLProfile):

    def execute_flow(self):  # pylint: disable=arguments-differ
        """
        Main flow for EBSL_06
        """
        self.state = 'RUNNING'
        try:
            super(EBSL06Profile, self).execute_flow()
            if self.is_cluster_configured('str') and self.is_cluster_configured('ebs'):
                self.create_celltrace_ebsl_subscription(STREAM_01_SUBSCRIPTION_NAME)
            else:
                self.add_error_as_exception(EnvironWarning('Required STR and/or EBS Clusters not found.'))
        except Exception as e:
            self.add_error_as_exception(e)
