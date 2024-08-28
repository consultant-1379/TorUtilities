import time
from datetime import datetime
from functools import partial

from enmutils.lib import log
from enmutils.lib.cache import is_enm_on_cloud_native
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib import load_mgr
from enmutils_int.lib.enm_deployment import get_values_from_global_properties
from enmutils_int.lib.pm_subscriptions import StatisticalSubscription, Subscription
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile import PmSubscriptionProfile
from enmutils_int.lib.services.deployment_info_helper_methods import get_cloud_native_service_vip

SMRS_SFTP_SBG_IS_USERNAME = "m2m-sbg-is-pm"
GLOBAL_PROPERTIES_CM_VIP_ADDRESS_KEY = "svc_CM_vip_ipaddress"
ENABLE_PM_DATA = "pmdata:enable;"
DISABLE_PM_DATA = "pmdata:disable;"
GET_PM_DATA_STATUS = "pmdata:status;"
RESUME_PM_MEASUREMENTS = "resumePMMeasurements Sftp://{username}:{password}@{ip_address}{path}{node_name}/ 900 900"
SUSPEND_PM_MEASUREMENTS = "suspendPMMeasurements"


class PmStatisticalProfile(PmSubscriptionProfile, GenericFlow):
    OFFSET = 0

    def create_statistical_subscription(self):
        """
        Description:
        Create statistical subscription using the profile attributes.

        :return: Subscription Object
        :rtype: StatisticalSubscription
        """
        subscription = self.create_statistical_subscription_object()
        subscription.create()
        self.delete_nodes_from_netex_attribute()
        self.set_teardown(StatisticalSubscription, subscription.name, subscription.id, subscription.poll_scanners,
                          node_types=subscription.node_types)
        self.check_all_nodes_added_to_subscription(subscription)
        log.logger.debug("Subscription Created: {0}".format(subscription.name))
        return subscription

    def create_statistical_subscription_object(self):
        """
        Create Statistical Subscription object based on certain prerequisites

        :return: Subscription Object
        :rtype: StatisticalSubscription
        """
        subscription_name = self.identifier
        log.logger.debug("Attempting to create subscription: {0}".format(subscription_name))
        node_types = self.NUM_NODES.keys()
        cbs, criteria = self.set_values_from_cbs()
        profile_nodes = self.get_profile_nodes(cbs=cbs)
        subscription_description = self.set_subscription_description()

        poll_scanners = getattr(self, "POLL_SCANNERS", False)

        subscription = StatisticalSubscription(
            name=subscription_name,
            cbs=cbs,
            description=subscription_description,
            user=self.USER,
            poll_scanners=poll_scanners,
            nodes=getattr(self, 'nodes_from_netex', profile_nodes),
            rop_enum=getattr(self, 'ROP_STR', 'FIFTEEN_MIN'),
            num_counters=getattr(self, 'NUM_COUNTERS', None),
            mo_class_counters_excluded=getattr(self, 'MO_CLASS_COUNTERS_EXCLUDED', None),
            criteria_specification=criteria,
            technology_domain_counter_limits=getattr(self, "TECHNOLOGY_DOMAIN_COUNTER_LIMITS", None),
            mo_class_counters_included=getattr(self, "MO_CLASS_COUNTERS_INCLUDED", None),
            mo_class_sub_counters_included=getattr(self, "MO_CLASS_SUB_COUNTERS_INCLUDED", None),
            reserved_counters=getattr(self, "RESERVED_COUNTERS", None),
            definer=getattr(self, "DEFINER", None),
            node_types=node_types)
        return subscription

    def check_statistical_system_subscription(self, pattern, user):
        """
        PM profiles calling this:
        27, 30, 31

        Description:
        Retrieve the statistical system subscription under test and check whether it is correct.

        :param pattern: Pattern that identifies the type of system defined subscription.
        :type pattern: str
        :param user: User instance
        :type user: enmutils.lib.enm_user_2.User
        """
        log.logger.debug("Checking that System Defined Subscription exists")
        system_subscription_name = Subscription.get_system_subscription_name_by_pattern(pattern, user)

        system_subscription = StatisticalSubscription(name=system_subscription_name, user=user)
        self.check_system_subscription_activation(system_subscription)

    def execute_additional_pm_profile_tasks(self):
        """
        Execute additional tasks as part of System Defined Subscription

        """
        log.logger.debug("Execute additional tasks as part of System Defined Subscription")

        if hasattr(self, "NUM_NODES") and "SBG-IS" in self.NUM_NODES.keys():
            log.logger.debug("SBG-IS Nodes need to be configured to enable PM files to be pushed from Netsim to SMRS.")

            node_attributes = ["node_id", "netsim", "simulation", "primary_type", "node_name"]
            nodes = self.all_nodes_in_workload_pool(node_attributes=node_attributes)
            log.logger.debug("Number of SBG-IS nodes found: {0}".format(len(nodes)))

            self.disable_pm_on_sbg_is_nodes(nodes)

            self.configure_smrs_upload_on_sbg_is_nodes(nodes)

            self.teardown_list.append(partial(picklable_boundmethod(self.disable_pm_on_sbg_is_nodes)))

        log.logger.debug("Execution of additional tasks as part of System Defined Subscription complete")

    def disable_pm_on_sbg_is_nodes(self, nodes=None):
        """
        Disable PM on all SBG-IS nodes

        :param nodes: List of Nodes
        :type nodes: list
        """

        log.logger.debug("Disabling PM on all SBG-IS nodes to ensure no residual measurements are active on any node")

        node_attributes = ["node_id", "netsim", "simulation", "primary_type", "node_name"]
        nodes = nodes if nodes else self.all_nodes_in_workload_pool(node_attributes=node_attributes)

        self.create_and_execute_threads(nodes, len(nodes), func_ref=self.disable_pm_on_sbg_is_node, args=[self])

    def configure_smrs_upload_on_sbg_is_nodes(self, nodes_list):
        """
        Configure SMRS SFTP Upload on {0} Nodes

        :param nodes_list: List of Node objects
        :type nodes_list: list
        """
        node_type = "SBG-IS"
        log.logger.debug("Configure SMRS SFTP Upload on {0} Nodes".format(node_type))

        cm_vip_ip_address = self.get_cm_vip_ipaddress()

        smrs_sftp_sbg_is_password = self.get_smrs_sftp_password(node_type)

        self.create_and_execute_threads(nodes_list, len(nodes_list), func_ref=self.enable_pm_on_sbg_is_node,
                                        args=[self, cm_vip_ip_address, smrs_sftp_sbg_is_password])

        log.logger.debug("Configuration of SMRS SFTP Upload on SBG-IS Nodes complete")

    def get_smrs_sftp_password(self, node_type):
        """
        Fetch the SMRS SFTP password from ENM

        :param node_type: Type of NetworkElement
        :type node_type: str
        :return: SMRS SFTP password
        :rtype: str
        :raises EnmApplicationError: if ENM doesnt provided expected SMRS SFTP password
        """
        log.logger.debug("Fetch SMRS SFTP password for {0} user from ENM".format(SMRS_SFTP_SBG_IS_USERNAME))

        smrs_sftp_password = None

        cmd = "secadm ftp get --netype {node_type}".format(node_type=node_type)
        try:
            enm_output = self.USER.enm_execute(cmd, timeout_seconds=120).get_output()
        except Exception as e:
            raise EnmApplicationError("Problem encountered trying to execute secadm command ('{0}') successfully - {1}"
                                      .format(cmd, e))

        if "Command Executed Successfully" in enm_output and "Password" in enm_output:
            smrs_sftp_password = str(enm_output[1])

        if not smrs_sftp_password:
            raise EnmApplicationError("SMRS password not set - check command '{0}' and see log file".format(cmd))

        log.logger.debug("SMRS SFTP password is: {}".format(smrs_sftp_password))
        return smrs_sftp_password

    @staticmethod
    def get_cm_vip_ipaddress():
        """
        Fetch the value of the CM_VIP_ipaddress key from ENM

        :return: IP address value of the CM_VIP_ipaddress key
        :rtype: str
        :raises EnmApplicationError: if ENM doesnt provided expected IP address
        """
        cm_vip_ip_address = ""
        if is_enm_on_cloud_native():
            cm_vip_ip_address = get_cloud_native_service_vip("mscm")

        else:
            log.logger.debug("Fetch the IP address of the {0} key from the ENM Global Properties File "
                             .format(GLOBAL_PROPERTIES_CM_VIP_ADDRESS_KEY))

            cm_vip_ip_address_values = get_values_from_global_properties(GLOBAL_PROPERTIES_CM_VIP_ADDRESS_KEY)
            if cm_vip_ip_address_values:
                cm_vip_ip_address = cm_vip_ip_address_values[0]
        if not cm_vip_ip_address:
            raise EnmApplicationError("No CM VIP ipaddress set on ENM - see log file")
        log.logger.debug("The IP address obtained from the ENM: {0}".format(cm_vip_ip_address))
        return cm_vip_ip_address

    @staticmethod
    def enable_pm_on_sbg_is_node(node, profile, cm_vip_ip_address, smrs_sftp_password):
        """
        Enable PM on SBG-IS Node
        :param node: Node Object
        :type node: `enmutils_int.lib.load_node.BaseLoadNode`
        :param profile: Profile object
        :type profile: `PmStatisticalProfile`
        :param cm_vip_ip_address: CM VIP IP Address
        :type cm_vip_ip_address: str
        :param smrs_sftp_password: SMRS SFTP Password
        :type smrs_sftp_password: str
        :return: Boolean to indicate if PM was enabled and resumed on the node
        :rtype: bool
        :raises EnvironError: if PM could not be enabled
        """
        log.logger.debug("Enabling PM on node: {0}".format(node.node_id))

        resume_pm_measurements_cmd = (RESUME_PM_MEASUREMENTS
                                      .format(username=SMRS_SFTP_SBG_IS_USERNAME, password=smrs_sftp_password,
                                              ip_address=cm_vip_ip_address, path="/smrsroot/pm/sbg-is/",
                                              node_name=node.node_id))

        if (profile.execute_netsim_command_on_netsim_node([node], ENABLE_PM_DATA) and
                profile.execute_netsim_command_on_netsim_node([node], resume_pm_measurements_cmd) and
                profile.get_node_pmdata_status(node, profile)):
            return True

        log.logger.debug("Problem encountered while enabling PM on node: {0}".format(node.node_id))

        raise EnvironError("Problem encountered during PM setup of SMRS Upload on SBG-IS node")

    @staticmethod
    def disable_pm_on_sbg_is_node(node, profile):
        """
        Disable PM on SBG-IS Node

        :param node: Node Object
        :type node: `enmutils_int.lib.load_node.BaseLoadNode`
        :param profile: Profile object
        :type profile: `PmStatisticalProfile`
        """
        log.logger.debug("Disabling PM on node: {0}".format(node.node_id))

        profile.execute_netsim_command_on_netsim_node([node], SUSPEND_PM_MEASUREMENTS)
        profile.execute_netsim_command_on_netsim_node([node], DISABLE_PM_DATA)
        profile.get_node_pmdata_status(node, profile)

    @staticmethod
    def get_node_pmdata_status(node, profile):
        """
        get node pm data enable/disable status

        :param node: Node Object
        :type node: `enmutils_int.lib.load_node.BaseLoadNode`
        :param profile: Profile object
        :type profile: `PmStatisticalProfile`
        :return: Result of operation
        :rtype: boolean
        """
        log.logger.debug("Getting PM status on node: {0}".format(node.node_id))
        return profile.execute_netsim_command_on_netsim_node([node], GET_PM_DATA_STATUS)

    def execute_flow(self, **kwargs):
        """
        Description:
        Call the superclass flow. Keyword arguments forwarded.
        If a subscription name is set for the profile, it's a system subscription that should already exist on the
        system. Otherwise, it's an user defined statistical subscription that needs to be created by the profile.
        """
        try:
            super(PmStatisticalProfile, self).execute_flow(**kwargs)
            self.state = 'RUNNING'
            if hasattr(self, 'SYS_DEF_SUB_PATTERN'):
                # System defined subscription
                self.check_statistical_system_subscription(self.SYS_DEF_SUB_PATTERN, user=self.USER)
                self.execute_additional_pm_profile_tasks()
            else:
                # User defined subscription
                subscription = self.create_statistical_subscription()
                log.logger.debug("Activating subscription")
                subscription.activate()
        except Exception as e:
            self.delete_nodes_from_netex_attribute()
            self.add_error_as_exception(e)

    @staticmethod
    def delay_execution_until_other_profile_started(other_profile_to_wait_for, time_to_wait_in_secs):
        """
        This function will cause execution to sleep for a period of time after a required profile has started

        :param other_profile_to_wait_for: name of the profile to check when it was started
        :type other_profile_to_wait_for: String
        :param time_to_wait_in_secs: period of time that this profile needs to wait for
        :type time_to_wait_in_secs: int
        """
        log.logger.debug("Waiting for {} to be started before this profile can proceed"
                         .format(other_profile_to_wait_for))

        load_mgr.wait_for_setup_profile(other_profile_to_wait_for, state_to_wait_for="COMPLETED", timeout_mins=240)
        start_time_of_other_profile = load_mgr.get_start_time_of_profile(other_profile_to_wait_for)

        if start_time_of_other_profile:
            time_now = datetime.now()
            elapsed_time_since_start_of_other_profile = int(
                (time_now - start_time_of_other_profile).total_seconds())
            if elapsed_time_since_start_of_other_profile < time_to_wait_in_secs:
                time_delay = time_to_wait_in_secs - elapsed_time_since_start_of_other_profile
                log.logger.debug("Sleeping for {0}s delay after profile {1} has started"
                                 .format(time_to_wait_in_secs, other_profile_to_wait_for))
                time.sleep(time_delay)

    def execute_offset_flow(self, profile_to_wait_for):
        """
        Description:
        Profiles that needs to wait for another profile execution run this flow.
        Create a statistical subscription and activate/disable it with an interval defined by SCHEDULE_SLEEP profile
        attribute.

        :param profile_to_wait_for Name of Profile to wait for
        :type profile_to_wait_for: str
        """
        self.state = 'SLEEPING'
        self.delay_execution_until_other_profile_started(profile_to_wait_for, self.OFFSET)

        self.state = 'RUNNING'
        try:
            super(PmStatisticalProfile, self).execute_flow()
            subscription = self.create_statistical_subscription()
        except Exception as e:
            self.delete_nodes_from_netex_attribute()
            self.add_error_as_exception(e)
        else:
            while self.keep_running():
                try:
                    log.logger.debug("Fetching state of subscription")
                    profile_state = subscription.get_subscription()['administrationState']
                    log.logger.debug("State of subscription is currently {0}".format(profile_state))

                    if profile_state == "INACTIVE":
                        log.logger.debug("Activating subscription")
                        subscription.activate()
                        log.logger.debug("Profile will now sleep until next iteration before deactivating "
                                         "subscription")
                    elif profile_state == "ACTIVE":
                        log.logger.debug("Deactivating subscription")
                        subscription.deactivate()
                        log.logger.debug("Profile will now sleep until next iteration before activating "
                                         "subscription")
                    else:
                        message = ("Unexpected subscription state {0}. Profile only expects either ACTIVE or "
                                   "INACTIVE states. This may indicate that an ENM problem exists and it should "
                                   "be investigated.".format(profile_state))
                        log.logger.debug(message)
                        raise EnmApplicationError(message)

                except Exception as e:
                    self.add_error_as_exception(e)

                log.logger.debug("Sleeping until next iteration")
                self.sleep()
