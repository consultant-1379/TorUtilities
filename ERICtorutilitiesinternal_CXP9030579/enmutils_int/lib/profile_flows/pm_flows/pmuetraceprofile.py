from functools import partial

from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib.pm_subscriptions import UETraceSubscription, Subscription
from enmutils_int.lib.profile_flows.pm_flows.pmsubscriptionprofile import PmSubscriptionProfile
from enmutils_int.lib.services.deploymentinfomanager_adaptor import get_pib_value_on_enm, update_pib_parameter_on_enm


class PmUETraceProfile(PmSubscriptionProfile):

    def enable_config_collection(self, config):
        """
        Run a command to set a configuration parameter value to 'true' on all the pm services in the system

        :param config: Name of the configuration parameter to update.
        :type config: str
        """
        update_pib_parameter_on_enm(enm_service_name="pmserv", pib_parameter_name=config, pib_parameter_value="true")
        log.logger.debug("Config collection {0} is enabled".format(config))
        self.teardown_list.append(partial(picklable_boundmethod(self.disable_config_collection), config))

    def disable_config_collection(self, config=None):
        """
         Run a command to set a configuration parameter value to 'false' on all the pm services in the system

         :param config: Name of the configuration parameter to update.
         :type config: str
         """
        update_pib_parameter_on_enm(enm_service_name="pmserv", pib_parameter_name=config, pib_parameter_value="false")
        log.logger.debug("Config collection {0} is disabled".format(config))

    def check_and_enable_config_collection(self):
        """
        checks the ctumCollectionEnabled enable or not in pib, if ctumCollectionEnabled value not enabled in pib then
        ctumCollectionEnabled value set to true in pib .
        If any error throws while enabling the ctumCollectionEnabled value and it returns False otherwise returns True.

        :return: boolean to indicate if ctumCollectionEnabled cant be set in pib
        :rtype: bool
        """
        config_collection_status = True
        is_ctum_enabled = get_pib_value_on_enm("pmserv", "ctumCollectionEnabled")
        is_ctum_enabled = False if is_ctum_enabled == "false" else True
        if not is_ctum_enabled:
            log.logger.warning("'ctumCollectionEnabled' is set to 'false'. Profile is now trying to enable it...")
            try:
                self.enable_config_collection("ctumCollectionEnabled")
            except:
                self.add_error_as_exception(EnmApplicationError("Can't set 'ctumCollectionEnabled' to 'true'."))
                config_collection_status = False

        return config_collection_status

    def check_uetrace_system_subscription(self, pattern, user):
        """
        Retrieve the uetrace system subscription under test and check whether it is correct.
        The subscription requires the 'ctumCollectionEnabled' system parameter enable and, at least,
        one SGSN-MME node in the network with 'mobileCountryCode' and 'mobileNetworkCode' attributes set.

        :param pattern: Pattern that identifies the type of system defined subscription
        :type pattern: str
        :param user: User instance
        :type user: enmutils.lib.enm_user_2.User
        """
        log.logger.debug("Checking that System Defined Subscription exists")
        system_subscription_name = Subscription.get_system_subscription_name_by_pattern(pattern, user)

        system_subscription = UETraceSubscription(name=system_subscription_name, ue_info=self.UE_INFO, user=self.USER,
                                                  poll_scanners=self.POLL_SCANNERS if hasattr(
                                                      self, 'POLL_SCANNERS') else False)
        config_collection_status = self.check_and_enable_config_collection()
        if config_collection_status:
            if system_subscription.sgsn_mme_exists_and_is_synchronized(self.USER):
                self.check_system_subscription_activation(system_subscription, pattern)
            else:
                self.add_error_as_exception(EnvironError('No synchronized SGSN-MME detected on server - '
                                                         'UETrace subscription not possible'))

    def create_uetrace_subscription(self):
        """
        Create and activate an uetrace subscription using the profile attributes.
        The subscription requires, at least, one SGSN-MME node in the network with 'mobileCountryCode' and 'mobileNetworkCode' attributes set.
        """
        default_interface_types = {'SGSN': ["s1_mme", "s3_s16", "s6a", "s11", "sv"], 'ENODEB': []}
        subscription_name = self.identifier
        subscription = UETraceSubscription(name=subscription_name,
                                           ue_info=self.UE_INFO,
                                           description=self.set_subscription_description(),
                                           user=self.USER,
                                           poll_scanners=self.POLL_SCANNERS if hasattr(
                                               self, 'POLL_SCANNERS') else False,
                                           rop_enum=self.ROP_STR if hasattr(self, 'ROP_STR') else 'FIFTEEN_MIN',
                                           interface_types=self.INTERFACE_TYPES if hasattr(self, 'INTERFACE_TYPES') else default_interface_types)

        if subscription.sgsn_mme_exists_and_is_synchronized(self.USER):
            subscription.create()
            self.teardown_list.append(subscription)
            subscription.activate()
        else:
            self.add_error_as_exception(EnvironError('No synchronized SGSN-MME detected on server - '
                                                     'No UETrace subscription can be created'))

    def execute_flow(self, **kwargs):
        """
        Call the superclass flow. Keyword arguments forwarded.
        If a subscription name is set for the profile, it's a system subscription that should already exist on the system.
        Otherwise, it's an user defined uetrace subscription that needs to be created by the profile,
        which also asserts that the 'ueTraceCollectionEnabled' system parameter is enabled beforehand.
        """
        try:
            super(PmUETraceProfile, self).execute_flow()
            self.state = 'RUNNING'
            if hasattr(self, 'SYS_DEF_SUB_PATTERN'):
                # System defined subscription
                self.check_uetrace_system_subscription(self.SYS_DEF_SUB_PATTERN, user=self.USER)
            else:
                # User defined subscription
                self.enable_config_collection("ueTraceCollectionEnabled")
                self.create_uetrace_subscription()
        except Exception as e:
            self.add_error_as_exception(e)
