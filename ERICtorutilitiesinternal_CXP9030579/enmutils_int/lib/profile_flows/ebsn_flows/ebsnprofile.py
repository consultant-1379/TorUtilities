from functools import partial

from enmutils.lib import log, cache
from enmutils.lib.exceptions import EnvironWarning, EnmApplicationError
from enmutils_int.lib.common_utils import get_internal_file_path_for_import
from enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile import PmSubscriptionProfile
from enmutils_int.lib.pm_subscriptions import CelltraceSubscription
from enmutils_int.lib.flexible_counter_management import (verify_creation_or_deletion_flex_counters_status,
                                                          remove_any_existing_flexible_counters,
                                                          import_flex_counters_in_enm)
from enmutils_int.lib.services.deploymentinfomanager_adaptor import get_pib_value_on_enm
from enmutils_int.lib import load_mgr
from enmutils_int.lib.profile_flows.common_flows.common_flow import is_enm_on_rack


FILE_01_SUBSCRIPTION_NAME = 'EBSN_FILE_01_CellTrace_subscription'
STREAMING_CLUSTER_VIP_IP = "eba_EBA_vip_ipaddress"
STR_CLUSTER_NOT_EXISTS_MESSAGE = ("This profile requires an Events (Streaming) "
                                  "Cluster configured in this ENM deployment "
                                  "in order to create a Celltrace Subscription "
                                  "(with category: CELLTRACE_NRAN_AND_EBSN_STREAM) in PMIC. "
                                  "Given that a Streaming Cluster is NOT currently configured, "
                                  "this profile is not applicable to this deployment.")


class EBSNProfile(PmSubscriptionProfile):

    USER = None

    def create_and_activate_celltrace_ebsn_subscription(self, subscription_name):
        """
        Create and Activate an CellTrace subscription with EBS flag enabled.

        :param subscription_name: Name of the subscription.
        :type subscription_name: str.
        """
        profile_nodes = self.get_all_nodes_in_workload_pool_based_on_node_filter()
        log.logger.debug("Number of nodes to be used by the profile: {0}".format(len(profile_nodes)))
        poll_scanners = getattr(self, "POLL_SCANNERS", False)
        node_types = self.NUM_NODES.keys()
        subscription = CelltraceSubscription(name=subscription_name,
                                             description=self.set_subscription_description(),
                                             user=self.USER,
                                             poll_scanners=poll_scanners,
                                             nodes=profile_nodes,
                                             rop_enum=getattr(self, 'ROP_STR', 'FIFTEEN_MIN'),
                                             num_counters=getattr(self, 'NUM_COUNTERS', None),
                                             num_events=getattr(self, 'NUM_EVENTS', 3),
                                             output_mode=getattr(self, 'OUTPUT_MODE', 'FILE'),
                                             ebs_enabled='true',
                                             cell_trace_category=getattr(self, 'CELL_TRACE_CATEGORY', None),
                                             event_filter=getattr(self, 'EVENT_FILTER', None),
                                             ebs_events=getattr(self, 'EBS_EVENTS', None),
                                             technology_domain=getattr(self, 'TECHNOLOGY_DOMAIN', None),
                                             node_types=node_types,
                                             definer=getattr(self, "DEFINER", None))
        subscription.create()
        self.set_teardown(CelltraceSubscription, subscription_name, subscription.id, poll_scanners,
                          node_types=subscription.node_types)
        self.check_all_nodes_added_to_subscription(subscription)
        subscription.activate()


class EBSN01Profile(EBSNProfile):

    def execute_flow(self):  # pylint: disable=arguments-differ
        """
        Main flow for EBSN_01
        """
        log.logger.debug("Waiting for EBSN_04 to be started before this profile can proceed")
        load_mgr.wait_for_setup_profile("EBSN_04", state_to_wait_for="COMPLETED", sleep_between=60, timeout_mins=30)
        self.state = 'RUNNING'
        message = ("For {0} deployment, This profile requires an {1} configured in this ENM deployment But {1} is "
                   "NOT currently configured")
        try:
            self.USER = self.create_users(1, roles=self.USER_ROLES, fail_fast=False, retry=True)[0]
            if cache.is_enm_on_cloud_native():
                cluster_name = "value_pack_ebs_ln"
                error_message = message.format('cENM', "value_pack_ebs_ln Tag")
            else:
                cluster_name = "evt"
                error_message = message.format('pENM' if cache.is_host_physical_deployment() else 'vENM',
                                               "Events (EVT) Cluster")
            if self.is_cluster_configured(cluster_name):
                subscription_name = '_'.join([FILE_01_SUBSCRIPTION_NAME, self.get_timestamp_str()])
                self.create_and_activate_celltrace_ebsn_subscription(subscription_name)
            else:
                self.add_error_as_exception(EnvironWarning(error_message))
        except Exception as e:
            self.add_error_as_exception(e)


class EBSN03Profile(EBSNProfile):
    FLEX_COUNTERS_FILE_PATH = get_internal_file_path_for_import("etc", "data", "flex_counters_50.json")

    def execute_flow(self):   # pylint: disable=arguments-differ
        """
        Main flow for  EBSN_03
        """
        log.logger.debug("Waiting for EBSN_05 to be started before this profile can proceed")
        load_mgr.wait_for_setup_profile("EBSN_05", state_to_wait_for="COMPLETED", sleep_between=60, timeout_mins=30)
        self.state = 'RUNNING'

        try:
            self.USER = self.create_users(1, roles=self.USER_ROLES, fail_fast=False, retry=True)[0]
            pib_value = get_pib_value_on_enm("pmserv", "pmicEbsStreamClusterDeployed")
            if pib_value == "true":
                log.logger.debug("Value of pib parameter pmicEbsStreamClusterDeployed "
                                 "is as expected: {0}".format(pib_value))
                self.create_and_activate_celltrace_ebsn_subscription(self.NAME)
            else:
                raise EnvironWarning(STR_CLUSTER_NOT_EXISTS_MESSAGE)
        except Exception as e:
            self.add_error_as_exception(e)


class EBSN04Profile(EBSNProfile):

    TOTAL_IMPORTED_FLEX_COUNTERS = 0
    FLEX_COUNTERS_FILE_PATH = get_internal_file_path_for_import("etc", "data",
                                                                "flex_counters_1000.json")
    PIB_PARAMETER = None

    def execute_flow(self):  # pylint: disable=arguments-differ
        """
        Main flow for EBSN_04
        """
        self.state = 'RUNNING'
        try:
            self.USER = self.create_users(1, roles=self.USER_ROLES, fail_fast=False, retry=True)[0]
            cluster_name, error_message = self.get_cluster_and_error_message()
            if self.is_cluster_configured(cluster_name):
                pib_value = get_pib_value_on_enm("pmserv", self.PIB_PARAMETER)
                if pib_value == '3000':
                    self.FLEX_COUNTERS_FILE_PATH = get_internal_file_path_for_import("etc", "data",
                                                                                     "flex_counters_3000.json")
                perform_flex_counters_prerequisites(self)
                subscription_name = self.identifier
                self.create_and_activate_celltrace_ebsn_subscription(subscription_name)
            else:
                raise EnvironWarning(error_message)
        except Exception as e:
            self.add_error_as_exception(e)

    def get_cluster_and_error_message(self):
        """
        Get cluster name and error message, set pib parameters based on deployment type.
        :return: returns tuple of cluster name and error message.
        :rtype: tuple
        """
        message = ("For {0} deployment, This profile requires an {1} configured in this ENM deployment But {1} is "
                   "NOT currently configured")
        evt_cluster_info = ("evt", "Events (EVT) Cluster")
        if cache.is_enm_on_cloud_native():
            cluster_name = "value_pack_ebs_ln"
            error_message = message.format('cENM', "value_pack_ebs_ln Tag")
            self.PIB_PARAMETER = "pmFcmMaxNoOfFlexCountersFileXLCloudENM"
        elif is_enm_on_rack():
            cluster_name = evt_cluster_info[0]
            error_message = message.format('rENM', evt_cluster_info[1])
            self.PIB_PARAMETER = "pmFcmMaxNoOfFlexCountersFileENMOnRack"
        else:
            cluster_name = evt_cluster_info[0]
            error_message = message.format('pENM' if cache.is_host_physical_deployment() else 'vENM',
                                           evt_cluster_info[1])
            self.PIB_PARAMETER = "pmFcmMaxNoOfFlexCounters"

        return cluster_name, error_message


class EBSN05Profile(EBSNProfile):
    TOTAL_IMPORTED_FLEX_COUNTERS = 0
    FLEX_COUNTERS_FILE_PATH = get_internal_file_path_for_import("etc", "data", "flex_counters_50.json")

    def execute_flow(self):   # pylint: disable=arguments-differ
        """
        Main flow for EBSN_05
        """
        self.state = 'RUNNING'

        try:
            self.USER = self.create_users(1, roles=self.USER_ROLES, fail_fast=False, retry=True)[0]
            pib_value = get_pib_value_on_enm("pmserv", "pmicEbsStreamClusterDeployed")
            if str(pib_value).lower() == "true":
                log.logger.debug("Value of pib parameter pmicEbsStreamClusterDeployed "
                                 "is as expected: {0}".format(pib_value))
                pib_value = self.get_cluster_and_pib_value()
                if str(pib_value) == '500':
                    self.FLEX_COUNTERS_FILE_PATH = get_internal_file_path_for_import("etc", "data",
                                                                                     "flex_counters_500.json")
                perform_flex_counters_prerequisites(self)
                subscription_name = self.identifier
                self.create_and_activate_celltrace_ebsn_subscription(subscription_name)
            else:
                raise EnvironWarning("For pENM deployment, This profile requires an "
                                     "pmicEbsStreamClusterDeployed (streaming cluster) pib parameter "
                                     "value should be enabled But pmicEbsStreamClusterDeployed (streaming cluster) is "
                                     "disabled in the deployment.")
        except Exception as e:
            self.add_error_as_exception(e)

    def get_cluster_and_pib_value(self):
        """
        Check if the deployment is on ENM rack and read the respective PIB parameter.
        :return: returns the pib value.
        :rtype: str
        """

        return (get_pib_value_on_enm("pmserv", "pmFcmMaxNoOfFlexCountersStreamENMOnRack")
                if is_enm_on_rack() else get_pib_value_on_enm("pmserv", "pmFcmMaxNoOfFlexCountersStream"))


def perform_flex_counters_prerequisites(profile):
    """
    This method performs set of flex counters prerequisites.
    i.e. Removes existing flex counters in ENM,
    import flex counters using flex counters json file and creates in ENM,
    verify the status response of created flex counters
    :param profile: Profile object
    :type profile: `enmutils_int.lib.profile.Profile`
    """
    log.logger.debug('{0} profile name'.format(profile.identifier))
    remove_any_existing_flexible_counters(profile.USER, profile.SLEEP_TIME)
    verify_import_flex_counters_status(profile)
    verify_creation_or_deletion_flex_counters_status(profile.USER, profile.SLEEP_TIME, "create",
                                                     profile.TOTAL_IMPORTED_FLEX_COUNTERS)


def verify_import_flex_counters_status(profile):
    """
    Verify the import flex counters status
    :raises EnmApplicationError: if flex counters are failed while importing the flex counters file
    :param profile: Profile object
    :type profile: `enmutils_int.lib.profile.Profile`
    """
    flex_counters_import_status = import_flex_counters_in_enm(profile.USER, profile.FLEX_COUNTERS_FILE_PATH)
    if (flex_counters_import_status and "Total Failed Flex Counters" in flex_counters_import_status and
            "Total Flex Counters" in flex_counters_import_status):
        total_failed_flex_counters = int(flex_counters_import_status["Total Failed Flex Counters"])
        total_successful_flex_counters = int(flex_counters_import_status["Total Flex Counters"])
        profile.TOTAL_IMPORTED_FLEX_COUNTERS = total_failed_flex_counters + total_successful_flex_counters
        profile.teardown_list.append(partial(remove_any_existing_flexible_counters, profile.USER, profile.SLEEP_TIME))
        if total_failed_flex_counters == profile.TOTAL_IMPORTED_FLEX_COUNTERS:
            raise EnmApplicationError("{0} EBS Flex counters are failed while importing the flex counters to "
                                      "ENM".format(total_failed_flex_counters))
        elif total_failed_flex_counters != 0:
            profile.add_error_as_exception(EnmApplicationError(
                "{0} EBS Flex counters failed to import in ENM out of {1} flex counters in "
                "ENM".format(total_failed_flex_counters, profile.TOTAL_IMPORTED_FLEX_COUNTERS)))
