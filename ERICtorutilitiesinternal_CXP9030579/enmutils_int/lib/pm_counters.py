# ********************************************************************
# Name    : PM Counters
# Summary : Includes functions that deal with counter handling for
#            PM Subscriptions
# ********************************************************************

from operator import itemgetter

from enmutils.lib import log
from enmutils.lib.headers import JSON_SECURITY_REQUEST

COUNTERS_URL = "/pm-service/rest/pmsubscription/counters?mim={model_identities}&definer={definer}"


def get_tech_domain_counters_based_on_profile(subscription):
    """
    Get technology domain counters (for RadioNodes) based on profile name, like PM_38 or PM_48

    :param subscription: Subscription object
    :type subscription: enmutils_int.lib.pm_subscriptions.Subscription
    :return: list of technology domain counters
    :rtype: List
    """
    log.logger.debug("Selecting technology domain counters based on profile name")
    counters = []
    counters_for_all_technology_domains = get_counters_for_all_technology_domains(subscription)

    reserved_pm_counters = get_reserved_pm_counters(subscription, counters_for_all_technology_domains)

    if subscription.name.startswith("PM_38"):
        counters = filter_counters_for_pm38(subscription, counters_for_all_technology_domains, reserved_pm_counters)

    if subscription.name.startswith("PM_48"):
        log.logger.debug("Assigning reserved counters to PM_48")
        counters = reserved_pm_counters

    log.logger.debug("Number of technology domain counters selected for profile: {0}".format(len(counters)))
    return counters


def get_reserved_pm_counters(subscription, all_counters, tech_domain="EPS"):
    """
    Get list of names of the reserved PM counters for PM_48

    :param subscription: Subscription object
    :type subscription: enmutils_int.lib.pm_subscriptions.Subscription
    :param all_counters: Dictionary of counters from all technology types
    :type all_counters: dict
    :param tech_domain: Technology Domain
    :type tech_domain: str
    :return: List of counter names
    :rtype: list
    """
    reserved_counters_limit = subscription.reserved_counters.get(tech_domain)
    log.logger.debug("Reserving the first {0} {1} counters for PM_48".format(reserved_counters_limit, tech_domain))

    all_counters_sorted = sorted(all_counters.get(tech_domain), key=itemgetter("name"))
    reserved_radionode_pm_counters = all_counters_sorted[:reserved_counters_limit]

    log.logger.debug("PM Counters reserved: {0}".format(len(reserved_radionode_pm_counters)))
    return reserved_radionode_pm_counters


def filter_counters_for_pm38(subscription, all_counters, reserved_pm_counters):
    """
    Get list of names of the reserved PM counters for PM_48

    :param subscription: Subscription object
    :type subscription: enmutils_int.lib.pm_subscriptions.Subscription
    :param all_counters: Dictionary of counters from all technology types
    :type all_counters: dict
    :param reserved_pm_counters: List of reserved PM counters (for PM_48)
    :type reserved_pm_counters: list
    :return: List of counter names
    :rtype: list
    """
    log.logger.debug("Filtering counters for PM_38")
    limited_lists_of_counters = {}
    for technology_domain, counter_limit in subscription.technology_domain_counter_limits.items():
        if all_counters[technology_domain]:
            log.logger.debug("Filtering out reserved counters that may exist in list of {0} {1} counters"
                             .format(len(all_counters[technology_domain]), technology_domain))
            available_counters = [counter for counter in all_counters[technology_domain]
                                  if counter not in reserved_pm_counters]

            available_counters = sorted(available_counters, key=itemgetter("name"))
            log.logger.debug("Applying counter limit of {0} to remaining {1} {2} counters"
                             .format(counter_limit, len(available_counters), technology_domain))
            limited_lists_of_counters[technology_domain] = available_counters[:counter_limit]

    counters = filter_out_duplicate_counters(limited_lists_of_counters)
    log.logger.debug("Number of filtered counters (for PM_38): {0}".format(len(counters)))
    return counters


def filter_out_duplicate_counters(counters_for_all_tech_domains):
    """
    Filter out duplicate counters between all tech domains

    :param counters_for_all_tech_domains: Dictionary containing lists of counters for each tech domain
    :type counters_for_all_tech_domains: dict
    :return: List of unique counters across all tech domains
    :rtype: list
    """
    unique_counters = []
    log.logger.debug("Filtering out duplicate counters between all technology domains")
    for index, counter_list in enumerate(counters_for_all_tech_domains.values()):
        if not index:
            unique_counters.extend(counter_list)
        else:
            unique_counters.extend([counter for counter in counter_list if counter not in unique_counters])

    unique_counters = sorted(unique_counters, key=itemgetter("name"))
    log.logger.debug("Number of filtered counters (excluding duplicates): {0}".format(len(unique_counters)))
    return unique_counters


def get_counters_for_all_technology_domains(subscription):
    """
    Get all technology domain counters from ENM

    :param subscription: Subscription object
    :type subscription: enmutils_int.lib.pm_subscriptions.Subscription
    :return: dictionary with technology domain counters
    :rtype: dict

    """
    log.logger.debug("Fetching user_defined technology domain counters from ENM, using profile limits: {0}"
                     .format(subscription.technology_domain_counter_limits))

    counters_for_all_tech_domains = {domain_type: [] for domain_type
                                     in subscription.technology_domain_counter_limits.keys()}
    for domain_type in subscription.technology_domain_counter_limits.keys():
        nodes_having_domain_type = [node for node in subscription.parsed_nodes if node.get("technologyDomain") and
                                    domain_type in node["technologyDomain"]]

        if not nodes_having_domain_type:
            log.logger.debug("No nodes with technology domain {0} are available to subscription"
                             .format(domain_type))
            continue

        log.logger.debug("{0} nodes with technology domain {1} are available"
                         .format(len(nodes_having_domain_type), domain_type))
        tech_domain_counters = get_counters_for_tech_domain(subscription, domain_type, nodes_having_domain_type)

        counters_for_all_tech_domains[domain_type] = tech_domain_counters

    log.logger.debug("Total number of counters per technology domain: {0}".format(
        {tech_domain: len(counters) for tech_domain, counters in counters_for_all_tech_domains.items()}))

    return counters_for_all_tech_domains


def get_counters_for_tech_domain(subscription, technology_domain, nodes, node_type="RadioNode"):
    """
    Get list of Counters that are common to all Model ID's for selected nodes

    :param subscription: Subscription object
    :type subscription: enmutils_int.lib.pm_subscriptions.Subscription
    :param technology_domain: Type of Technology Domain
    :type technology_domain: str
    :param nodes: List of "Parsed Nodes" dictionaries
    :type nodes: list
    :param node_type: Node type
    :type node_type: str

    :return: List of common counters amongst all Model ID's
    :rtype: list
    """
    log.logger.debug("Fetching user defined counters for all model id's for technology domain: {0}"
                     .format(technology_domain))

    model_ids_per_tech_domain = list(set(node["ossModelIdentity"] for node in nodes))
    log.logger.debug("Model ID's from applicable nodes: {0}".format(model_ids_per_tech_domain))

    user_defined_counters = {}
    for model_id in model_ids_per_tech_domain:
        enm_counters = fetch_counters_from_enm_per_model_id(subscription, node_type, model_id, technology_domain)

        if not enm_counters:
            log.logger.debug("No counters returned from ENM")
            continue

        user_defined_counters[model_id] = filter_counters(subscription, technology_domain, enm_counters)

    tech_domain_counters = ((filter_common_counters_for_model_ids(user_defined_counters)
                             if len(model_ids_per_tech_domain) > 1
                             else user_defined_counters[model_ids_per_tech_domain[0]])
                            if user_defined_counters else [])

    log.logger.debug("Number of {0} counters: {1}".format(technology_domain, len(tech_domain_counters)))
    return tech_domain_counters


def fetch_counters_from_enm_per_model_id(subscription, node_type, model_id, technology_domain):
    """
    Fetch counters from ENM for a particular Model ID*

    :param subscription: Subscription object
    :type subscription: enmutils_int.lib.pm_subscriptions.Subscription
    :param node_type: Node Type
    :type node_type: str
    :param model_id: Oss Model Identity
    :type model_id: str
    :param technology_domain: Technology Domain
    :type technology_domain: str
    :return: List of Counters
    :rtype: list
    """
    log.logger.debug("Fetching supported counters from ENM for Model ID: {0}".format(model_id))
    model_id_string = ("{node_type}:{model_id}:{technology_domain}"
                       .format(node_type=node_type, model_id=model_id, technology_domain=technology_domain))

    response = subscription.user.get(COUNTERS_URL.format(
        model_identities=model_id_string, definer="NE"), headers=JSON_SECURITY_REQUEST)

    enm_counters = response.json()
    log.logger.debug("Counters returned by ENM: {0}".format(len(enm_counters)))
    return enm_counters


def filter_common_counters_for_model_ids(user_defined_counters):
    """
    Filter common counters for set of model id's

    :param user_defined_counters: Dictionary of list of counters per different model id's
    :type user_defined_counters: dict
    :return: List of common counters
    :rtype: list
    """
    log.logger.debug("Determining common counters between all model id's")
    common_counters = []
    for index, counter_list in enumerate(user_defined_counters.values()):
        if not index:
            common_counters.extend(counter_list)
        else:
            for counter in common_counters:
                if counter not in counter_list:
                    common_counters.remove(counter)

    common_counters = sorted(common_counters, key=itemgetter("name"))
    log.logger.debug("{0} common user-defined counters".format(len(common_counters)))
    return common_counters


def filter_counters(subscription, technology_domain, counters):
    """
    Filter counters according to different criteria

    :param subscription: Subscription object
    :type subscription: enmutils_int.lib.pm_subscriptions.Subscription
    :param technology_domain: Technology Domain
    :type technology_domain: str
    :param counters: List of counters
    :type counters: list
    :return: List of filtered counters
    :rtype: list
    """
    log.logger.debug("Filtering counters according to different criteria")
    counters = filter_user_defined_counters(counters)

    if (getattr(subscription, "mo_class_counters_excluded", False) and
            subscription.mo_class_counters_excluded.get(technology_domain)):
        counters = filter_excluded_counters(counters, subscription.mo_class_counters_excluded.get(technology_domain))

    if (getattr(subscription, "mo_class_counters_included", False) and
            subscription.mo_class_counters_included.get(technology_domain)):
        counters = filter_included_counters(counters, subscription.mo_class_counters_included.get(technology_domain))

    log.logger.debug("{0} counters after criteria filtering completed".format(len(counters)))
    return counters


def filter_user_defined_counters(counters):
    """
    Filter counters to include User Defined counters only

    :param counters: List of counters
    :type counters: list
    :return: List of filtered counters
    :rtype: list
    """
    log.logger.debug("Filtering {0} counters to include USER_DEFINED counters only".format(len(counters)))

    filtered_counters = [{"moClassType": counter['sourceObject'], "name": counter['counterName']}
                         for counter in counters if counter['scannerType'] == 'USER_DEFINED']

    log.logger.debug("Number of USER_DEFINED counters: {0}".format(len(filtered_counters)))
    return filtered_counters


def filter_excluded_counters(counters, exclude_mo_classes):
    """
    Filter counters to exclude counters from certain MO classes

    :param counters: List of counters
    :type counters: list
    :param exclude_mo_classes: List of MO classes to be excluded
    :type exclude_mo_classes: list

    :return: List of filtered counters
    :rtype: list
    """

    log.logger.debug('Filtering {0} counters to exclude counters from the following {1} MO Class(es): {2}'
                     .format(len(counters), len(exclude_mo_classes),
                             ','.join(class_name for class_name in exclude_mo_classes)))

    filtered_counters = [counter for counter in counters if counter['moClassType'] not in exclude_mo_classes]

    log.logger.debug("Number of filtered counters (excluding specified classes): {0}".format(len(filtered_counters)))
    return filtered_counters


def filter_included_counters(counters, include_mo_classes):
    """
    Filter counters to include counters from certain MO classes only

    :param counters: List of counters
    :type counters: list
    :param include_mo_classes: List of MO classes to restrict the counters to
    :type include_mo_classes: list

    :return: List of filtered counters
    :rtype: list
    """
    log.logger.debug('Filtering {0} counters to include counters from the following {1} MO Class(es) only: {2}'
                     .format(len(counters), len(include_mo_classes),
                             ','.join(class_name for class_name in include_mo_classes)))

    filtered_counters = [counter for counter in counters if counter['moClassType'] in include_mo_classes]

    log.logger.debug("Number of filtered counters (including specified classes): {0}".format(len(filtered_counters)))
    return filtered_counters
