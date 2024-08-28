# ********************************************************************
# Name    : Topology Browser
# Summary : Functional module used TOP_01 profile. Allows the user
#           to retrieve the topology home page, navigate the help,
#           core functionality is to update attributes on LTE cells
#           using the topology application
# ********************************************************************

import json
import time
from random import choice
from enmutils.lib import log
from enmutils.lib.exceptions import NetworkTopologyError

HEADERS = {'Content-Type': 'application/json; charset=utf-8'}


def go_to_topology_browser_home(user):
    """
    Navigate to topology browser.
    :param user: instance of ENM user
    :type user: `enmutils.lib.enm_user_2.User`
    """
    topology_home_url = "/#topologybrowser"
    response = user.get(topology_home_url, verify=False)
    time.sleep(1)
    response.raise_for_status()


def step_through_topology_browser_node_tree_to_nrcelldu(user, node_poid, node_id):
    """
    User walks through topology browser through a set of get requests till they hit NRCellDU
    :param user: ENM user instance to be used to perform the flow
    :type user: `enmutils.lib.enm_user_2.User`
    :param node_poid: PO ID of node
    :type node_poid: str
    :param node_id: ID of node
    :type node_id: str

    :raises NetworkTopologyError: if the expected MO is not found at the current level of topology browser

    :return: json of either NRCellDU
    :rtype: dict
    """
    # Network expand before this point.

    # Click a node
    topology_browser_node_url = "/#topologybrowser?poid={0}".format(node_poid)
    response = user.get(topology_browser_node_url, verify=False)
    response.raise_for_status()
    time.sleep(1)

    # Expand the node

    topology_browser_expand_node = "/persistentObject/network/{0}".format(node_poid)

    managed_element_request = user.get(topology_browser_expand_node)
    time.sleep(1)
    managed_element_request.raise_for_status()
    managed_element_json = managed_element_request.json()
    managed_element_poid = ""

    for mo in managed_element_json['treeNodes'][0]['childrens']:
        if mo['moType'] == 'ManagedElement':
            managed_element_poid = mo['poId']

    # Click ManagedElement
    if managed_element_poid:  # Node has ManagedElement..
        topology_browser_managed_element_url = "/#topologybrowser?poid={0}".format(managed_element_poid)
        response = user.get(topology_browser_managed_element_url, verify=False)
        response.raise_for_status()
        time.sleep(1)

        # Expand ManagedElement
        topology_browser_expand_managed_element = "/persistentObject/network/{0}".format(managed_element_poid)
        gnbdufunction_request = user.get(topology_browser_expand_managed_element)
        time.sleep(1)
        gnbdufunction_request.raise_for_status()
        gnbdufunction_json = gnbdufunction_request.json()
    else:  # Node has no ManagedElement. RadioNodes have no ManagedElement
        gnbdufunction_json = managed_element_json

    try:
        gnbdufunction_poid = [gnbdufunction['poId'] for gnbdufunction in gnbdufunction_json['treeNodes'][0]['childrens'] if gnbdufunction['moType'] == 'GNBDUFunction'][0]
    except IndexError:
        raise NetworkTopologyError("No GNBDUFunction can be found on node {0}".format(node_id))

    # Click GNBCUUPFunction
    topology_browser_gnbdufunction_url = "/#topologybrowser?poid={0}".format(gnbdufunction_poid)
    response = user.get(topology_browser_gnbdufunction_url, verify=False)
    response.raise_for_status()
    time.sleep(1)

    # Expand GNBCUUPFunction
    topology_browser_expand_gnbdufunction = "/persistentObject/network/{0}".format(gnbdufunction_poid)

    nrcelldu_request = user.get(topology_browser_expand_gnbdufunction)
    time.sleep(1)
    nrcelldu_request.raise_for_status()
    nrcelldu_json = nrcelldu_request.json()

    try:
        nrcelldu_info = [nrcelldu for nrcelldu in nrcelldu_json['treeNodes'][0]['childrens'] if nrcelldu['moType'] == 'NRCellDU'][0]
    except IndexError:
        raise NetworkTopologyError("No cell information could be found on node {0}".format(node_id))

    # Click NRCellCU
    nrcelldu_poid = nrcelldu_info['poId']
    topology_browser_gnbdufunction_url = "/#topologybrowser?poid={0}".format(nrcelldu_poid)
    nrcelldu_get_attributes_request_url = "/persistentObject/{0}".format(nrcelldu_poid)

    nrcelldu_attributes_request = user.get(nrcelldu_get_attributes_request_url)
    nrcelldu_attributes_request.raise_for_status()
    nrcelldu_attributes = nrcelldu_attributes_request.json()
    user.get(topology_browser_gnbdufunction_url, verify=False)
    time.sleep(1)

    return nrcelldu_attributes


def step_through_topology_browser_node_tree_to_nrcellcu(user, node_poid, node_id):
    """
    User walks through topology browser through a set of get requests till they hit NRCellCU
    :param user: ENM user instance to be used to perform the flow
    :type user: `enmutils.lib.enm_user_2.User`
    :param node_poid: PO ID of node
    :type node_poid: str
    :param node_id: ID of node
    :type node_id: str

    :raises NetworkTopologyError: if the expected MO is not found at the current level of topology browser

    :return: json of either NRCellCU
    :rtype: dict
    """
    # Network expanded before this point.

    # Click a node
    topology_browser_node_url = "/#topologybrowser?poid={0}".format(node_poid)
    response = user.get(topology_browser_node_url, verify=False)
    response.raise_for_status()
    time.sleep(1)

    # Expand the node

    topology_browser_expand_node = "/persistentObject/network/{0}".format(node_poid)

    managed_element_request = user.get(topology_browser_expand_node)
    time.sleep(1)
    managed_element_request.raise_for_status()
    managed_element_json = managed_element_request.json()
    managed_element_poid = ""

    for mo in managed_element_json['treeNodes'][0]['childrens']:
        if mo['moType'] == 'ManagedElement':
            managed_element_poid = mo['poId']

    # Click ManagedElement
    if managed_element_poid:  # Node has ManagedElement..
        topology_browser_managed_element_url = "/#topologybrowser?poid={0}".format(managed_element_poid)
        response = user.get(topology_browser_managed_element_url, verify=False)
        response.raise_for_status()
        time.sleep(1)

        # Expand ManagedElement
        topology_browser_expand_managed_element = "/persistentObject/network/{0}".format(managed_element_poid)
        cranfunction_request = user.get(topology_browser_expand_managed_element)
        time.sleep(1)
        cranfunction_request.raise_for_status()
        cranfunction_json = cranfunction_request.json()
    else:  # Node has no ManagedElement. RadioNodes have no ManagedElement
        cranfunction_json = managed_element_json
    try:
        cranfunction_poid = [cranfunction['poId'] for cranfunction in cranfunction_json['treeNodes'][0]['childrens'] if cranfunction['moType'] == 'GNBCUCPFunction'][0]
    except IndexError:
        raise NetworkTopologyError("No GNBCUCPFunction can be found on node {0}".format(node_id))

    # Click GNBCUCPFunction
    topology_browser_gnbdufunction_url = "/#topologybrowser?poid={0}".format(cranfunction_poid)
    response = user.get(topology_browser_gnbdufunction_url, verify=False)
    response.raise_for_status()
    time.sleep(1)

    # Expand GNBCUCPFunction
    topology_browser_expand_gnbdufunction = "/persistentObject/network/{0}".format(cranfunction_poid)

    nrcellcu_request = user.get(topology_browser_expand_gnbdufunction)
    time.sleep(1)
    nrcellcu_request.raise_for_status()
    nrcellcu_json = nrcellcu_request.json()

    try:
        nrcellcu_info = [nrcellcu for nrcellcu in nrcellcu_json['treeNodes'][0]['childrens'] if nrcellcu['moType'] == 'NRCellCU'][0]
    except IndexError:
        raise NetworkTopologyError("No cell information could be found on node {0}".format(node_id))

    # Click NRCellCU
    nrcellcu_poid = nrcellcu_info['poId']
    topology_browser_cranfunction_url = "/#topologybrowser?poid={0}".format(nrcellcu_poid)
    nrcellcu_get_attributes_request_url = "/persistentObject/{0}".format(nrcellcu_poid)

    nrcellcu_attributes_request = user.get(nrcellcu_get_attributes_request_url)
    nrcellcu_attributes_request.raise_for_status()
    nrcellcu_attributes = nrcellcu_attributes_request.json()
    user.get(topology_browser_cranfunction_url, verify=False)
    time.sleep(1)

    return nrcellcu_attributes


def step_through_topology_browser_node_tree_to_eutrancellfdd_or_eutrancelltdd(user, node_poid,
                                                                              node_id):
    """
    User walks through topology browser through a set of get requests till they hit EUtranCellFDD or EUtranCellTDD
    :param user: ENM user instance to be used to perform the flow
    :type user: `enmutils.lib.enm_user_2.User`
    :param node_poid: PO ID of node
    :type node_poid: str
    :param node_id: ID of node
    :type node_id: str

    :raises NetworkTopologyError: if the expected MO is not found at the current level of topology browser

    :return: json of either EUtranCellFDD or EUtranCellTDD
    :rtype: dict
    """
    # Network expanded before this point.

    # Click a node
    topology_browser_node_url = "/#topologybrowser?poid={0}".format(node_poid)
    response = user.get(topology_browser_node_url, verify=False)
    response.raise_for_status()
    time.sleep(1)

    # Expand the node

    topology_browser_expand_node = "/persistentObject/network/{0}".format(node_poid)

    managed_element_request = user.get(topology_browser_expand_node)
    time.sleep(1)
    managed_element_request.raise_for_status()
    managed_element_json = managed_element_request.json()
    managed_element_poid = ""

    for mo in managed_element_json['treeNodes'][0]['childrens']:
        if mo['moType'] == 'ManagedElement':
            managed_element_poid = mo['poId']

    # Click ManagedElement
    if managed_element_poid:  # Node has ManagedElement..
        topology_browser_managed_element_url = "/#topologybrowser?poid={0}".format(managed_element_poid)
        response = user.get(topology_browser_managed_element_url, verify=False)
        response.raise_for_status()
        time.sleep(1)

        # Expand ManagedElement
        topology_browser_expand_managed_element = "/persistentObject/network/{0}".format(managed_element_poid)
        enodeBFunction_request = user.get(topology_browser_expand_managed_element)
        time.sleep(1)
        enodeBFunction_request.raise_for_status()
        enodeBFunction_json = enodeBFunction_request.json()
    else:  # Node has no ManagedElement. RadioNodes have no ManagedElement
        enodeBFunction_json = managed_element_json

    try:
        enodeBFunction_poId = [enodeBFunction['poId'] for enodeBFunction in enodeBFunction_json['treeNodes'][0]['childrens'] if enodeBFunction['moType'] == 'ENodeBFunction'][0]
    except IndexError:
        raise NetworkTopologyError("No ENodeBFunction can be found on node {0}".format(node_id))

    # Click ENodeBFunction
    topology_browser_enodbfunction_url = "/#topologybrowser?poid={0}".format(enodeBFunction_poId)
    response = user.get(topology_browser_enodbfunction_url, verify=False)
    response.raise_for_status()
    time.sleep(1)

    # Expand ENodeBFunction
    topology_browser_expand_enodbfunction = "/persistentObject/network/{0}".format(enodeBFunction_poId)

    eutrancell_request = user.get(topology_browser_expand_enodbfunction)
    time.sleep(1)
    eutrancell_request.raise_for_status()
    eutrancell_json = eutrancell_request.json()

    try:
        eutrancell_info = [eutrancell for eutrancell in eutrancell_json['treeNodes'][0]['childrens'] if eutrancell['moType'] == 'EUtranCellFDD' or eutrancell['moType'] == 'EUtranCellTDD'][0]
    except IndexError:
        raise NetworkTopologyError("No cell information could be found on node {0}".format(node_id))

    # Click EUtranCellFDD or EUtranCellTDD
    eutrancell__poId = eutrancell_info['poId']
    topology_browser_enodbfunction_url = "/#topologybrowser?poid={0}".format(eutrancell__poId)
    eutrancell_get_attributes_request_url = "/persistentObject/{0}".format(eutrancell__poId)

    eutrancell_attributes_request = user.get(eutrancell_get_attributes_request_url)
    eutrancell_attributes_request.raise_for_status()
    eutrancell_attributes = eutrancell_attributes_request.json()
    user.get(topology_browser_enodbfunction_url, verify=False)
    time.sleep(1)

    return eutrancell_attributes


def update_random_attribute_on_eutrancellfdd_or_eutrancelltdd(eutrancell_attributes, user, attribute_default=None,
                                                              action=""):
    """
    Builds a json payload and sends a put request to update an attribute on the cell.

    :param eutrancell_attributes: json for EUtranCellFDD or EUtranCellTDD.
    :type eutrancell_attributes: dict
    :param user: instance of ENM user
    :type user: `enmutils.lib.enm_user_2.User`
    :param attribute_default: default value of attribute before change
    :type attribute_default: dict
    :param action: Action to be performed (modify/undo)
    :type action: str

    :return: value of attribute to be changed
    :rtype: dict
    """

    attributes_values_dict = {'dl256QamEnabled': [False,
                                                  "BOOLEAN"],
                              'drxActive': [True,
                                            "BOOLEAN"],
                              'highSpeedUEActive': [True,
                                                    "BOOLEAN"],
                              'eutranCellCoverage': [[{"key": "posCellBearing", "value": -1, "datatype": "INTEGER"},
                                                      {"key": "posCellOpeningAngle", "value": -1,
                                                       "datatype": "INTEGER"},
                                                      {"key": "posCellRadius", "value": 1000, "datatype": "INTEGER"}],
                                                     "COMPLEX_REF"]}

    eutrancell_poId = eutrancell_attributes['poId']
    fdn = eutrancell_attributes['fdn']
    attribute_to_change = choice(attributes_values_dict.keys())

    attributes_list = [a_val for a_val in eutrancell_attributes['attributes']]
    default_attribute = {}

    for attribute in attributes_list:
        if attribute_to_change in attribute.values():
            default_attribute = attribute

    attribute_value = attributes_values_dict[attribute_to_change][0]
    data_type = attributes_values_dict[attribute_to_change][1]

    if action == "UNDO":
        attribute_to_change = attribute_default['key']
        attribute_value = attribute_default['value']

        if attribute_to_change == 'eutranCellCoverage':
            for child_attribute in attribute_value:
                if child_attribute['datatype'] is None:
                    child_attribute['datatype'] = 'INTEGER'

        data_type = attributes_values_dict[attribute_to_change][1]

    update_attribute_json = {"poId": eutrancell_poId,
                             "fdn": fdn,
                             "attributes": [{"key": "{attribute_to_change}".format(attribute_to_change=attribute_to_change),
                                             "value": attribute_value,
                                             "datatype": data_type}]}

    update_attribute_url = "/persistentObject/{0}".format(eutrancell_poId)
    data = json.dumps(update_attribute_json)
    log.logger.debug("PUT {0} with data: {1}".format(attribute_to_change, data))

    response = user.put(update_attribute_url, data=data, headers=HEADERS)
    response.raise_for_status()

    return default_attribute


def update_random_attribute_on_nrcelldu(nrcelldu_attributes, user, attribute_default=None, action=""):
    """
    Builds a json payload and sends a put request to update an attribute on the cell.

    :param nrcelldu_attributes: json for NRCellDU.
    :type nrcelldu_attributes: dict
    :param user: instance of ENM user
    :type user: `enmutils.lib.enm_user_2.User`
    :param attribute_default: default value of attribute before change
    :type attribute_default: dict
    :param action: Action to be performed (modify/undo)
    :type action: str

    :return: value of attribute to be changed
    :rtype: dict
    """

    attributes_values_dict = {'bfrEnabled': [False, "BOOLEAN"],
                              'dl256QamEnabled': [False, "BOOLEAN"],
                              'drxEnable': [False, "BOOLEAN"],
                              'endcUlLegSwitchEnabled': [True, "BOOLEAN"]}

    nrcelldu_poid = nrcelldu_attributes['poId']
    fdn = nrcelldu_attributes['fdn']
    attribute_to_change = choice(attributes_values_dict.keys())

    attributes_list = [a_val for a_val in nrcelldu_attributes['attributes']]
    default_attribute = {}

    for attribute in attributes_list:
        if attribute_to_change in attribute.values():
            default_attribute = attribute

    attribute_value = attributes_values_dict[attribute_to_change][0]
    data_type = attributes_values_dict[attribute_to_change][1]

    if action == "UNDO":
        attribute_to_change = attribute_default['key']
        attribute_value = attribute_default['value']
        data_type = attributes_values_dict[attribute_to_change][1]

    update_attribute_json = {"poId": nrcelldu_poid,
                             "fdn": fdn,
                             "attributes": [{"key": "{attribute_to_change}".format(attribute_to_change=attribute_to_change),
                                             "value": attribute_value,
                                             "datatype": data_type}]}

    update_attribute_url = "/persistentObject/{0}".format(nrcelldu_poid)
    data = json.dumps(update_attribute_json)
    log.logger.debug("PUT {0} with data: {1}".format(attribute_to_change, data))

    response = user.put(update_attribute_url, data=data, headers=HEADERS)
    response.raise_for_status()

    return default_attribute


def update_random_attribute_on_nrcellcu(nrcellcu_attributes, user, attribute_default=None, action=""):
    """
    Builds a json payload and sends a put request to update an attribute on the cell.

    :param nrcellcu_attributes: json for NRCellCU.
    :type nrcellcu_attributes: dict
    :param user: instance of ENM user
    :type user: `enmutils.lib.enm_user_2.User`
    :param attribute_default: default value of attribute before change
    :type attribute_default: dict
    :param action: Action to be performed (modify/undo)
    :type action: str

    :return: value of attribute to be changed
    :rtype: dict
    """

    attributes_values_dict = {'hiPrioDetEnabled': [False, "BOOLEAN"],
                              'mcpcPCellEnabled': [False, "BOOLEAN"],
                              'mcpcPSCellEnabled': [False, "BOOLEAN"],
                              'pmUeIntraFreqEnabled': [True, "BOOLEAN"]}

    nrcellcu_poid = nrcellcu_attributes['poId']
    fdn = nrcellcu_attributes['fdn']
    attribute_to_change = choice(attributes_values_dict.keys())
    attributes_list = [a_val for a_val in nrcellcu_attributes['attributes']]
    default_attribute = {}

    for attribute in attributes_list:
        if attribute_to_change in attribute.values():
            default_attribute = attribute

    attribute_value = attributes_values_dict[attribute_to_change][0]
    data_type = attributes_values_dict[attribute_to_change][1]

    if action == "UNDO":
        attribute_to_change = attribute_default['key']
        attribute_value = attribute_default['value']
        data_type = attributes_values_dict[attribute_to_change][1]

    update_attribute_json = {"poId": nrcellcu_poid,
                             "fdn": fdn,
                             "attributes": [{"key": "{attribute_to_change}".format(attribute_to_change=attribute_to_change),
                                             "value": attribute_value,
                                             "datatype": data_type}]}

    update_attribute_url = "/persistentObject/{0}".format(nrcellcu_poid)
    data = json.dumps(update_attribute_json)
    log.logger.debug("PUT {0} with data: {1}".format(attribute_to_change, data))

    response = user.put(update_attribute_url, data=data, headers=HEADERS)
    response.raise_for_status()

    return default_attribute


def navigate_topology_browser_app_help(user):
    """
    Navigate around topology browser app help.
    :param user: instance of ENM user
    :type user: `enmutils.lib.enm_user_2.User`
    """
    topology_browser_app_help = "/#help/app/topologybrowser"
    what_is_topology_browser_url = "/#help/app/topologybrowser/concept/faq"
    traverse_a_tree_tutorial_url = "#help/app/topologybrowser/concept/tutorials/tutorial02"
    edit_node_attributes_help_url = "#help/app/topologybrowser/concept/tutorials/tutorial03"

    top_help_requests = [topology_browser_app_help, what_is_topology_browser_url, traverse_a_tree_tutorial_url,
                         edit_node_attributes_help_url]

    for req in top_help_requests:
        response = user.get(req, verify=False)
        time.sleep(1)
        response.raise_for_status()
