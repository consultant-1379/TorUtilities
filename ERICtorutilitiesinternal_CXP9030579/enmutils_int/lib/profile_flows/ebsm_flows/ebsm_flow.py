from enmutils.lib import cache
from enmutils.lib.exceptions import EnvironWarning
from enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile import PmSubscriptionProfile
from enmutils_int.lib.pm_subscriptions import EBMSubscription
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class EBSM04Profile(GenericFlow):

    EVT_CLUSTER_EBS_TAG_NOT_EXISTS_MESSAGE = ("For {0} deployment, This profile requires an {1} configured "
                                              "in this ENM deployment, in order to create an "
                                              "'EBM and EBS-M Subscription' in PMIC. Given that an {1} is NOT "
                                              "currently configured, this profile is not applicable to this "
                                              "deployment. Profile PM_20 handles the 'EBM Subscription' instead.")

    def execute_flow(self):
        """
        Main flow for EBSM_04
        """
        try:
            user = self.create_profile_users(1, self.USER_ROLES, retry=True)[0]
            if cache.is_enm_on_cloud_native():
                cluster_name = "value_pack_ebs_m"
                error_message = self.EVT_CLUSTER_EBS_TAG_NOT_EXISTS_MESSAGE.format('cENM', "value_pack_ebs_m Tag")
            else:
                cluster_name = "evt"
                error_message = self.EVT_CLUSTER_EBS_TAG_NOT_EXISTS_MESSAGE.format(
                    'pENM' if cache.is_host_physical_deployment() else 'vENM', "Events (EVT) Cluster")

            pm_sub_profile = PmSubscriptionProfile()
            if pm_sub_profile.is_cluster_configured(cluster_name):
                # Generation of EBS Counter Files will be enabled by this subscription
                # i.e. Subscription Type in PMIC will be "EBM and EBS-M"
                self.state = 'RUNNING'
                self.create_and_activate_ebsm_subscription(user)
            else:
                self.add_error_as_exception(EnvironWarning(error_message))
        except Exception as e:
            self.add_error_as_exception(e)

    def create_and_activate_ebsm_subscription(self, user):
        """
        Create and Activate ebsm subscription in enm

        :type user: enm_user_2.User
        :param user: User instance
        """
        nodes_list = self.get_nodes_list_by_attribute(node_attributes=["node_id", "poid", "primary_type"])
        subscription = EBMSubscription("{0}".format(self.identifier),
                                       description="ebsm_04_load_profile_18A",
                                       num_events=self.NUM_EVENTS,
                                       num_counters=self.NUM_COUNTERS,
                                       user=user,
                                       poll_scanners=self.POLL_SCANNERS if hasattr(
                                           self, 'POLL_SCANNERS') else False,
                                       nodes=nodes_list,
                                       ebs_enabled="true",
                                       ebs_output_strategy=self.COUNTER_FILE_FORMAT,
                                       rop_enum=self.EBM_ROP_INTERVAL,
                                       definer=getattr(self, "DEFINER", None))
        try:
            subscription.create()
            teardown_subscription = EBMSubscription("{0}".format(self.identifier))
            teardown_subscription.id = subscription.id
            self.teardown_list.append(teardown_subscription)
            subscription.activate()
        except Exception as e:
            self.add_error_as_exception(e)
