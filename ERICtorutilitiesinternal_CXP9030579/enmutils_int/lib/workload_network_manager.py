# ********************************************************************
# Name    : Workload Network Manager
# Summary : Responsible for determining the network values to be
#           applied on start up. Allows the workload tool to determine
#           the type and size of the ENM deployment, and selecting the
#           related network configuration file, provides functionality
#           to detect number of cells, detect transport, extra small
#           networks, perform sync check of the deployment and return
#           the values of the configuration files to be applied.
# ********************************************************************
from enmutils.lib import log, persistence, config
import enmutils_int.lib.node_pool_mgr as node_pool_mgr
from enmutils_int.lib.nrm_default_configurations import profile_values
from enmutils_int.lib.services import deployment_info_helper_methods as helper
from enmutils_int.lib.services.deployment_info_helper_methods import (EXTRA_SMALL_NETWORK, FIVE_K_NETWORK,
                                                                      FIFTEEN_K_NETWORK, FORTY_K_NETWORK,
                                                                      SIXTY_K_NETWORK, SOEM_5K_NETWORK,
                                                                      TRANSPORT_10K_NETWORK, TRANSPORT_20K_NETWORK)

NE_TYPES = {"RAN": ["5GRadioNode", "MSRBS_V1", "RadioNode", "ERBS", "RBS", "RNC", "BSC"],
            "TRANSPORT": ["Router6274", "Router6672", "Router6675", "SIU02", "CISCO-ASR900", "CISCO-ASR9000",
                          "FRONTHAUL-6020", "FRONTHAUL-6080", "JUNIPER-MX", "JUNIPER-PTX", "JUNIPER-SRX",
                          "JUNIPER-vMX", "JUNIPER-vSRX", "MINI-LINK-6351", "MINI-LINK-6352", "MINI-LINK-6366",
                          "MINI-LINK-665x", "MINI-LINK-669x", "MINI-LINK-CN210", "MINI-LINK-CN510R1",
                          "MINI-LINK-CN510R2", "MINI-LINK-CN810R1", "MINI-LINK-CN810R2", "MINI-LINK-Indoor",
                          "MINI-LINK-PT2020", "TCU02", "Switch-6391", "ESC", "SCU"]}
NETWORK_CELL_COUNT = 'network-cell-count'
NETWORK_TYPE = 'network-type'


def map_synonym_to_network_size(network_synonym):
    """
    Convenient mapper between set of values and particular network key(specified in the profile_values.py)

    :param network_synonym: Value to be mapped to a network key
    :type network_synonym: str

    :rtype: str
    :returns: Mapped network key for a requested network
    """
    key_extra_small = EXTRA_SMALL_NETWORK
    key_5k = FIVE_K_NETWORK
    key_5k_soem = SOEM_5K_NETWORK
    key_15k = FIFTEEN_K_NETWORK
    key_40k = FORTY_K_NETWORK
    key_60k = SIXTY_K_NETWORK
    key_20k_transport = TRANSPORT_20K_NETWORK
    key_10k_transport = TRANSPORT_10K_NETWORK

    value_network_mapper = dict.fromkeys([EXTRA_SMALL_NETWORK, 'extra-small', '1k', '1'], key_extra_small)
    value_network_mapper.update(dict.fromkeys([FIVE_K_NETWORK, '5k', '5'], key_5k))
    value_network_mapper.update(dict.fromkeys([FIFTEEN_K_NETWORK, '15k', '15'], key_15k))
    value_network_mapper.update(dict.fromkeys([FORTY_K_NETWORK, '40k', '40'], key_40k))
    value_network_mapper.update(dict.fromkeys([SIXTY_K_NETWORK, '60k', '60'], key_60k))
    value_network_mapper.update(dict.fromkeys([SOEM_5K_NETWORK, '5k_soem', 'soem'], key_5k_soem))
    value_network_mapper.update(dict.fromkeys([TRANSPORT_20K_NETWORK, '20k_transport'],
                                              key_20k_transport))
    value_network_mapper.update(dict.fromkeys([TRANSPORT_10K_NETWORK, '10k_transport'],
                                              key_10k_transport))

    mapped = value_network_mapper.get(network_synonym.lower(), None)

    if not mapped:
        log.logger.error("ERROR, Network: {0} doesn't map to any supported network. Supported values are: {1}".format(
            network_synonym, ', '.join(sorted(value_network_mapper.keys()))))
    return mapped


def get_all_networks():
    """
    Return dictionary with all networks.

    :rtype: dict
    :return: dictionary with all networks
    """
    return profile_values.networks


def detect_transport_network_and_set_transport_size():
    """
    Determine if the NetworkElement neTypes indicate a Transport network
    """
    if config.has_prop("DEFAULT_VALUES") and not config.get_prop("DEFAULT_VALUES"):
        log.logger.debug("Default values disabled, configuration value already supplied.")
        return
    try:
        ne_type_dict = helper.sort_and_count_ne_types()
    except Exception as e:
        log.logger.info("Could not determine network type, error encountered:: [{0}].Load will be applied based upon "
                        "the network cell count.".format(str(e)))
        return
    if set(ne_type_dict.keys()).intersection(NE_TYPES.get("RAN")):
        log.logger.info("RAN NetworkElement(s) found, load will be applied based upon the network cell count.")
    elif set(ne_type_dict.keys()).intersection(NE_TYPES.get("TRANSPORT")):
        log.logger.info("Transport NetworkElement(s) found, determining transport configuration to be used.")
        determine_size_of_transport_network(ne_type_dict)
    else:
        log.logger.info("Could not determine network type, load will be applied based upon the network cell count.")


def determine_size_of_transport_network(ne_type_dict):
    """
    Count the total transport NetworkElement neTypes and select the applicable transport configuration
    """
    total_transport_nodes = 0
    for key, value in ne_type_dict.items():
        if key in NE_TYPES.get("TRANSPORT"):
            total_transport_nodes += value
    log.logger.debug("Total transport count\t{0}.".format(total_transport_nodes))
    transport_flag = SOEM_5K_NETWORK if total_transport_nodes <= 5000 else (TRANSPORT_10K_NETWORK if
                                                                            total_transport_nodes <= 10000 else
                                                                            TRANSPORT_20K_NETWORK)
    config.set_prop('DEFAULT_VALUES', False)
    config.set_prop('network_config', transport_flag)


class InputData(object):

    FIVE_K = map_synonym_to_network_size('5')
    FIFTEEN_K = map_synonym_to_network_size('15')
    FORTY_K = map_synonym_to_network_size('40')
    SIXTY_K = map_synonym_to_network_size('60')
    TEN_K_TRANSPORT = map_synonym_to_network_size('10k_transport')
    TWENTY_K_TRANSPORT = map_synonym_to_network_size('20k_transport')
    EXTRA_K = map_synonym_to_network_size('1')
    EXTRA_SMALL = 1200
    FIVE_K_NETWORK_SIZE = 7500
    FIFTEEN_K_NETWORK_SIZE = 27500
    FORTY_K_NETWORK_SIZE = 50000

    def __init__(self):
        """
        Initialise method of the class

        """
        self.pool = node_pool_mgr.get_pool() or {}
        self.networks = get_all_networks()
        self.ignore_warning = False

    @property
    def get_all_exclusive_profiles(self):
        """
        Retrieves the profiles names which have the EXCLUSIVE variable set

        :return: list, List of profile names
        :rtype: list
        """
        log.logger.debug("WorkloadNetworkMgr: Determine exclusive profiles from Network files")
        network = self.basic_network
        exclusive_profiles = []
        for app in network:
            for profile in network.get(app):
                if ("EXCLUSIVE" in network.get(app).get(profile).iterkeys() and
                        network.get(app).get(profile).get("SUPPORTED") and
                        network.get(app).get(profile).get('EXCLUSIVE') and self.get_profiles_values(app, profile)):

                    exclusive_profiles.append(profile)
        if not self.ignore_warning:
            log.logger.warn('Exclusive profile list: {0}'.format(exclusive_profiles))
        log.logger.debug("WorkloadNetworkMgr: Determine exclusive profiles from Network files - complete")
        return exclusive_profiles

    @property
    def network_size(self):
        return helper.get_total_cell_count()

    @property
    def network_key(self):
        network_size = self.network_size
        if not network_size:
            if not persistence.get(NETWORK_TYPE):
                detect_transport_network_and_set_transport_size()
            else:
                config.set_prop('network_config', persistence.get(NETWORK_TYPE))
        if config.has_prop('network_config'):
            return map_synonym_to_network_size(config.get_prop('network_config'))
        elif 0 < network_size <= self.EXTRA_SMALL:
            return self.EXTRA_K
        elif network_size and network_size <= self.FIVE_K_NETWORK_SIZE:
            return self.FIVE_K
        elif network_size and network_size <= self.FIFTEEN_K_NETWORK_SIZE:
            return self.FIFTEEN_K
        elif network_size > self.FORTY_K_NETWORK_SIZE:
            return self.SIXTY_K

        return self.FORTY_K

    @property
    def basic_network(self):
        return self.networks.get("basic")

    @property
    def network(self):
        network_key = self.network_key
        if not persistence.has_key(NETWORK_TYPE):
            log.logger.debug("Setting NETWORK_TYPE in persistence: {0}".format(network_key))
            persistence.set(NETWORK_TYPE, network_key, 21600, log_values=False)
        return self.networks.get(network_key)

    @property
    def default_config_values(self):
        """
        Property to indicate if default configuration values for a profile should be loaded.
        Profile values found in forty_k_network.py are the default values.
        :return: Select default config values.
        :rtype: bool
        """
        return config.get_prop('DEFAULT_VALUES') if config.has_prop('DEFAULT_VALUES') else True

    def get_profiles_values(self, app, profile):
        """
        Accesses and returns, the profile attributes to be set on the profile(s) with the start option.
        If a profile is not found in the initial config file and default_config_values is false no profile value will be returned.
        This is needed for deployments like SOEM and ExtraSmall to prevent non supported profiles from starting.

        :param app: str, Application name
        :type app: str
        :param profile: str, Name of the profile to return
        :type profile: str
        :rtype: dict
        :return: Dictionary, containing key,value pairs of attributes for profile
        """
        log.logger.debug("Fetching profile values from network config files for {0}".format(profile))
        profile = profile.upper()
        app = app.lower()
        network_keys = self.network
        values = self.robustness_check(profile, app)
        list1 = ['SECUI_11']
        if not values and app in network_keys:
            base_configuration_values = self.networks.get(self.FORTY_K).get(app).get(profile)
            restricted = self.network_key in [EXTRA_SMALL_NETWORK, SOEM_5K_NETWORK, TRANSPORT_10K_NETWORK,
                                              TRANSPORT_20K_NETWORK]
            if profile in network_keys.get(app).keys():
                values = network_keys.get(app).get(profile)
                if not values and profile not in list1:
                    log.logger.warn("Profile {1} is not supported in following deployment type : {0}".format(self.network_key, profile))
                    return None
            elif (base_configuration_values is not None and self.default_config_values and self.network_key and
                  not restricted):
                values = base_configuration_values
        return self.update_basic_values(values, profile, app)

    @staticmethod
    def robustness_check(profile, app):
        """
        Performs the check for Robustness config setting

        :param profile: Name of the profile to retrieve the basic network values
        :type profile: str
        :param app: Name of the application to retrieve the basic network values
        :type app: str

        :return: Found dictionary values if any were found and config property was set
        :rtype: dict|None
        """
        values = None
        if config.has_prop("ROBUSTNESS") and config.get_prop("ROBUSTNESS"):
            robust_config = helper.get_robustness_configuration()
            if app in robust_config and robust_config.get(app).get(profile):
                values = robust_config.get(app).get(profile)
        return values

    def update_basic_values(self, values, profile, app):
        """
        Update the found dictionary values with the basic network values

        :param values: Dictionary values found if any
        :type values: dict|None
        :param profile: Name of the profile to retrieve the basic network values
        :type profile: str
        :param app: Name of the application to retrieve the basic network values
        :type app: str

        :return: Updated values if any were provided
        :rtype: dict|None
        """
        if isinstance(values, dict):
            values.update(self.basic_network.get(app).get(profile))
        else:
            log.logger.debug('No profile values found for {0}. '
                             'Default config file checked: {1}'.format(profile, self.default_config_values))
        return values
