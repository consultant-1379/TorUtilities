# ********************************************************************
# Name    : Cell Management Application
# Summary : This is the primary module for interacting with Cell
#           Management application. Allows the user to query Cell
#           Management for inward and outward node relations, create
#           new relations, create CGI object, create new cells,
#           delete existing relations, delete existing cells, lock
#           and unlock cells.
# ********************************************************************

import json
import random
import re
import time
from time import sleep

from requests.exceptions import HTTPError, ConnectionError

from enmutils.lib import log, timestamp
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils.lib.exceptions import EnvironError, ScriptEngineResponseValidationError, EnmApplicationError
from enmutils.lib.headers import JSON_SECURITY_REQUEST
from enmutils_int.lib.cmcli import get_cell_attributes
from enmutils_int.lib.enm_user import get_workload_admin_user
from enmutils_int.lib.load_node import filter_nodes_having_poid_set
from enmutils_int.lib.node_pool_mgr import remove_gerancell_in_range

GET_LIST_OF_CELL_FDNs_ON_NODE = "cmedit get {node_name} {mo_type}"
BASE_URL = 'configuration-tasks/v1/tasks'
CELL_URL = 'cell-management-internal/v1/tasks'
NETWORK_PO_IDS_URL = '/persistentObject/network/-1?relativeDepth=0:-2&childDepth=1'

NEW = "NEW"
DEFAULT = "DEFAULT"
BATCH_MO_SIZE = 50  # Batch size to be used in queries to DPS for finding nodes with required number of cells
CELLMGT_CELL_NAME_IDENTIFIERS = ['CELLMGT-1', 'CELLMGT-2']
UTRAN_CID_RANGE = (1, 65536)


def modify_cell_parameters(user, cell_fdn, attribute_data):
    """
    Function to send the REST request to the Cell Management Service to order attribute changes on an LTE cell
    that will result in same attributes being set in neighbouring/adjacent LTE cells (ExternalEUtranCell MO).

    This ensures that the network remains consistent and that LTE-to-LTE call handovers
    will take place without without interruption

    :param user: `lib.enm_user_2.User` instance
    :type user: enm_user_2.User
    :param cell_fdn: FDN of the cell being changed
    :type cell_fdn: list
    :param attribute_data: dict containing the attributes and corresponding new values
    :type attribute_data: dict
    :return: list of affected MO's
    :rtype: list
    :raises HTTPError: raises if response is not ok
    """

    json_data = {
        "name": 'modifyCellParameters',
        "sourceFdn": cell_fdn,
        "attributes": attribute_data,
        "executionMode": "EXECUTE",
        "responseLevel": "HIGH"
    }
    log.logger.debug("# Request to be submitted to Cell Mgt Service: ")
    log.logger.debug(json.dumps(json_data))

    # Perform POST operation on Cell Mgt Service
    start = timestamp.get_current_time()
    response = user.post(BASE_URL, data=json.dumps(json_data), headers=JSON_SECURITY_REQUEST)
    finish = timestamp.get_current_time() - start
    if not response.ok:
        raise HTTPError("ENM POST request to {0} returned NOK status".format(BASE_URL), response=response)

    time_taken = timestamp.get_string_elapsed_time(finish)
    response_as_map = response.json()

    successfulMoOperationsData = response_as_map['successfulMoOperations']
    log.logger.debug('# Update to cell {cell_name} took {time_taken}s and resulted in {num_successful_ops} '
                     'successful MO Operations'.format(cell_name=get_cell_name(cell_fdn), time_taken=time_taken,
                                                       num_successful_ops=len(successfulMoOperationsData)))

    # Print out the updated ENM data to the debug logs
    list_of_affected_mos = [get_nodename_for_mo(mo_data['fdn']) for mo_data in successfulMoOperationsData]
    log.logger.debug("# EUtranCellFDD/ExternalEUtranCellFDD MO's on the following nodes were affected by the update: "
                     "{0}".format(list(list_of_affected_mos)))

    return list_of_affected_mos


def get_cell_name(cell_fdn):
    """
    Converts cell_fdn into cell_name
    :param cell_fdn: fdn of cell
    :type cell_fdn: list
    :return: cell name
    :rtype: str
    """
    return cell_fdn.split("=")[-1].strip()


def get_nodename_for_mo(fdn):
    """
    Gets Node name for MO FDN
    e.g.
    1) this MO:
        SubNetwork=ERBS-SUBNW-2,MeContext=ieatnetsimv6064-01_LTE01ERBS00157,ManagedElement=1,ENodeBFunction=1,
             EUtraNetwork=1,ExternalENodeBFunction=LTE01ERBS00108,ExternalEUtranCellFDD=LTE01ERBS00108-12
    exists on the following CPP Node:
         MeContext=ieatnetsimv6064-01_LTE01ERBS00157

    2) this MO:
        SubNetwork=NETSimW,ManagedElement=LTE06dg2ERBS00001,ENodeBFunction=1,EUtranCellFDD=LTE06dg2ERBS00001-1
    exists on the following RadioNode:
        ManagedElement=LTE06dg2ERBS00001


    :param fdn: MO fdn
    :type fdn: dict
    :return: Node Name
    :rtype: str
    """
    list_of_parts = fdn.split(",")

    if 'MeContext' in fdn:
        # MO is from a CPP Node
        for part in list_of_parts:
            if 'MeContext=' in part:
                return part.split("=")[-1].strip()
    else:
        # MO is from RadioNode
        for part in list_of_parts:
            if 'ManagedElement' in part:
                return part.split("=")[-1].strip()


def get_all_fdn_list_of_cells_on_node(user, node_name, mo_type):
    """
    Getting list of FDN's of all cells on a given node

    :param user: user: `lib.enm_user_2.User` instance
    :type user: enm_user_2.User
    :param node_name: Name of Node
    :type node_name: str
    :param mo_type: Type of MO
    :type mo_type: str
    :return: list: list of cell FDN's on a given node
    :rtype: list
    """

    response = user.enm_execute(GET_LIST_OF_CELL_FDNs_ON_NODE.format(node_name=node_name, mo_type=mo_type))
    output = response.get_output()

    cell_fdn_list = []
    for cell_fdn in [item for item in output if "FDN".lower() in item.lower()]:
        cell_fdn_list.append(cell_fdn.split(":")[1].strip())

    return cell_fdn_list


def configure_new_attribute_values(attribute_data, current_attribute_values, set_new_attributes_to_zero=False):
    """
    New values are decided upon for the attributes passed in "attribute_data" based off the "current attribute values"
    in ENM

    :param attribute_data: list of lists, with each inner list containing an attribute, its min value and max values
                           respectively e.g. ["physicalLayerCellIdGroup", 0, 167]
    :type attribute_data: list
    :param current_attribute_values: dictionary of attributes and their corresponding values currently existing on ENM
    :type current_attribute_values: dict
    :param set_new_attributes_to_zero: True if the attribute values are to be set to 0 else False
    :type set_new_attributes_to_zero: bool

    :return: new_attribute_values: dictionary of attributes and their newly configured values
    :rtype: dict
    """

    log.logger.debug('Attempting to configure new values for the attributes: "{0}" based off ENM\'s current attribute'
                     'values: "{1}" '.format([', '.join(attr[0] for attr in attribute_data)], current_attribute_values))

    new_attribute_values = {}

    # Go through each attribute (& their current values) in the dictionary passed in
    for attribute_name, attribute_value in current_attribute_values.items():
        # Check out each attribute to see what the value should be set to
        for attribute_data_info in attribute_data:
            if attribute_name == attribute_data_info[0]:
                value = _get_new_attribute_value(attribute_name, attribute_value, attribute_data_info,
                                                 set_new_attributes_to_zero)
                new_attribute_values[attribute_name] = value

    log.logger.debug('Successfully configured the new attribute values as follows: "{0}"'.format(new_attribute_values))

    return new_attribute_values


def _get_new_attribute_value(attribute_name, attribute_value, attribute_data, set_new_attributes_to_zero=False):
    """
    Get the new value that will be configured to the specified attribute "attribute_name"

    :param attribute_name: Name of the attribute to be modified
    :type attribute_name: str
    :param attribute_value: the value assigned currently to the attribute on ENM
    :type attribute_value: str
    :param attribute_data: list containing the attribute, its min value and max values
                        respectively e.g. ["physicalLayerCellIdGroup", 0, 167]
    :type attribute_data: list
    :param set_new_attributes_to_zero: True if the attribute values are to be set to 0 else False
    :type set_new_attributes_to_zero: bool

    :return: the new value that will be configured to the attribute
    :rtype: int
    """

    log.logger.debug(
        'Attempting to get the new value for attribute: "{}". Its current value on ENM is: "{}" '.format(
            attribute_name, attribute_value))

    if set_new_attributes_to_zero:
        new_value = 0
    else:
        # If the attribute value is a digit and has not reached its maximum value, increment the value by 1
        if attribute_value.isdigit() and int(attribute_value) < attribute_data[2]:
            new_value = int(attribute_value) + 1
        # Otherwise reset the value to its original default minimal value
        else:
            new_value = attribute_data[1]

    log.logger.debug('Successfully got the new value: "{}" for attribute: "{}" '.format(new_value, attribute_name))

    return new_value


def populate_node_cell_data(user, required_number_of_cells_per_node, mo_type, list_of_nodes, mo_attribute_data,
                            set_new_attributes_to_zero=False):
    """
    Function that will create a dictionary of dictionaries containing nodes,
        cell_fdn's and default & new attribute values
    e.g
    {
        node1: {
                cell_fdn1: {
                        DEFAULT: { attrA: value1A1, attrB: value1B1, attrC: value1C1, ...},
                        NEW: { attrA: value1A2, attrB: value1B2, attrC: value1C2, ... }
                },
                cell_fdn2: {
                        DEFAULT: { attrA: value2A1, attrB: value2B1, attrC: value2C1, ... },
                        NEW: { attrA: value2A2, attrB: value2B2, attrC: value2C2, ... },
                }
                ...
        },
        node2: {
                cell_fdn3: {
                        DEFAULT: { attrA: value3A1, attrB: value3B1, attrC: value3C1, ... },
                        NEW: { attrA: value3A2, attrB: value3B2, attrC: value3C2, ... }
                },
                cell_fdn4: {
                        DEFAULT: { attrA: value4A1, attrB: value4B1, attrC: value4C1, ... },
                        NEW: { attrA: value4A2, attrB: value4B2, attrC: value4C2, ... },
                },
                ...
        },
        ...
    }

    :param user: user instance
    :type user: enm_user_2.User
    :param required_number_of_cells_per_node: number of cells required per node
    :type required_number_of_cells_per_node: int
    :param mo_type: MO being used
    :type mo_type: str
    :param list_of_nodes: list of nodes to perform operation on
    :type list_of_nodes: list
    :param mo_attribute_data: MO attributes to be used
    :type mo_attribute_data: list
    :param set_new_attributes_to_zero: If true the new atrributes value will be set to 0
    :type set_new_attributes_to_zero: bool
    :return: dictionary of node & cell data
    :rtype: dict
    :raises EnvironError: raises if fdn list is not full
    """

    list_of_attributes = [attribute_data_info[0] for attribute_data_info in mo_attribute_data[mo_type]]

    node_cell_data = {}

    node_counter = cell_counter = 1

    for selected_node_info in list_of_nodes:
        node_name = selected_node_info.node_id

        required_cell_fdn_list = get_required_cell_fdn_list(node_name, node_counter, user, mo_type,
                                                            required_number_of_cells_per_node, node_cell_data)

        for cell_fdn in required_cell_fdn_list[node_name]:
            cell_name = get_cell_name(cell_fdn)

            if cell_fdn not in node_cell_data[node_name]:
                node_cell_data[node_name][cell_fdn] = {}

            if DEFAULT not in node_cell_data[node_name][cell_fdn]:
                node_cell_data[node_name][cell_fdn][DEFAULT] = {}
            if NEW not in node_cell_data[node_name][cell_fdn]:
                node_cell_data[node_name][cell_fdn][NEW] = {}

            log.logger.debug("# Fetching relevant attribute values for cell {cell_counter}: {cell_name}"
                             .format(cell_name=cell_name, cell_counter=cell_counter))
            # sleep for arbitrary time to avoid overloading cmserv
            time.sleep(1)
            attribute_data = get_cell_attributes(user, selected_node_info, cell_name, list_of_attributes, mo_type)
            if not attribute_data:
                return {}

            node_cell_data[node_name][cell_fdn][DEFAULT] = attribute_data

            log.logger.debug("# Default attribute values for {0}, {1}: {2}"
                             .format(node_name, cell_name, node_cell_data[node_name][cell_fdn][DEFAULT]))

            node_cell_data[node_name][cell_fdn][NEW] = configure_new_attribute_values(
                mo_attribute_data[mo_type],
                node_cell_data[node_name][cell_fdn][DEFAULT],
                set_new_attributes_to_zero)

            log.logger.debug("# New attribute values for {0}, {1}: {2}"
                             .format(node_name, cell_name, node_cell_data[node_name][cell_fdn][NEW]))

            cell_counter += 1

        node_counter += 1

    return node_cell_data


def get_required_cell_fdn_list(node_name, node_counter, user, mo_type,
                               required_number_of_cells_per_node, node_cell_data):
    """
    Return a full required cell FDN dictionary

    :param node_name: Name of the current node
    :type node_name: str
    :param node_counter: used to identify node number
    :type node_counter: int
    :param user: user instance
    :type user: enm_user_2.User
    :param mo_type: MO being used
    :type mo_type: str
    :param required_number_of_cells_per_node: number of cells required per node
    :type required_number_of_cells_per_node: int
    :param node_cell_data: contains node cell data
    :type node_cell_data: dict

    :rtype: Dict
    :return: Dictionary of Cell FDNs for node
    :raises EnvironError: raises if there is Unexpected ENM configuration
    """

    log.logger.debug("# Fetching list of Cell FDN's for node {node_counter}: {node_name}"
                     .format(node_name=node_name, node_counter=node_counter))

    full_cell_fdn_list = {node_name: get_all_fdn_list_of_cells_on_node(user, node_name, mo_type)}

    if not full_cell_fdn_list[node_name]:
        raise EnvironError('Unexpected ENM configuration - no cells on Node: {0}'.format(node_name))

    # Only require a subset of the possible number of cells on node
    required_cell_fdn_list = {node_name: full_cell_fdn_list[node_name][0:required_number_of_cells_per_node]}
    if node_name not in node_cell_data:
        node_cell_data[node_name] = {}

    log.logger.debug("# Full List of Cells for node {0} ({1}): {2}".format(
        node_name,
        node_counter,
        [get_cell_name(cell_fdn) for cell_fdn in full_cell_fdn_list[node_name]]))

    return required_cell_fdn_list


def update_cells_attributes_via_cell_management(user, run_type, required_number_of_nodes, node_cell_data):
    """
    Function containing the logic to execute the actual use case

    :param user: user instance
    :type user: enm_user_2.User
    :param run_type: either default or new, implying which set of attributes to be set
    :type run_type: str
    :param required_number_of_nodes: number of nodes required
    :type required_number_of_nodes: int
    :param node_cell_data: dict containing nodes, cell_fdn's, attributes and corresponding new & default values
    :type node_cell_data: dict

    :raises EnmApplicationError: raised if modify cell request fails
    """

    start = timestamp.get_current_time()

    list_of_nodes = node_cell_data.keys()
    exceptions = []

    node_counter = cell_counter = 1
    failed_cell_names = []
    for node_name in list_of_nodes:

        for cell_fdn in node_cell_data[node_name]:
            cell_name = get_cell_name(cell_fdn)

            log.logger.debug(
                "# {run_type} attribute values being set on node {node_counter}/{node_total_count}: "
                "{node_name}, cell {cell_counter}: {cell_name} ".format(run_type=run_type,
                                                                        cell_counter=cell_counter,
                                                                        cell_name=cell_name,
                                                                        node_counter=node_counter,
                                                                        node_total_count=required_number_of_nodes,
                                                                        node_name=node_name))
            try:
                modify_cell_parameters(user, cell_fdn, node_cell_data[node_name][cell_fdn][run_type])
            except Exception as e:
                failed_cell_names.append(cell_name)
                log.logger.debug(str(e))
                exceptions.append(e)

            cell_counter += 1

        node_counter += 1

    finish = timestamp.get_current_time() - start
    time_taken = timestamp.get_string_elapsed_time(finish)
    log.logger.debug("# This iteration took {time_taken}s to complete".format(time_taken=time_taken))
    if exceptions:
        raise EnmApplicationError("Iteration failed to change PCI values for {1} cells {0}, please check the logs for "
                                  "more information.".format(failed_cell_names, len(failed_cell_names)))


def revert_cell_attributes(cell_counter, cell_fdn, attribute_data, user=None):
    """
    Function that will revert the attribute values back to default during teardown

    :param user: user instance
    :type user: enm_user_2.User
    :param cell_counter: simple counter (indicating roughly what is being torn down)
    :type cell_counter: int
    :param cell_fdn: fdn of the cell
    :type cell_fdn: list
    :param attribute_data: dict containing default values of attributes
    :type attribute_data: dict
    """
    user = user or get_workload_admin_user()
    cell_name = get_cell_name(cell_fdn)
    log.logger.debug("{0} attribute values for cell {1} (i.e. cell number {2}) being restored as part of teardown"
                     .format(DEFAULT, cell_name, cell_counter))
    try:
        modify_cell_parameters(user, cell_fdn, attribute_data)
    except (HTTPError, ConnectionError) as e:
        log.logger.debug("Problem occurred during reset of attribute values for cell: {cell_name} - {exception}"
                         .format(cell_name=cell_name, exception=str(e)))


def log_config_error(node_count, cell_count):
    """
    Function to log error in case of network config problem

    :param node_count: number of nodes
    :type node_count: int
    :param cell_count: number of cells
    :type cell_count: int
    :return: string containing error info
    :rtype: str
    """

    config_error_text_0 = 'Network Config Problem: The required number of nodes ({0})'.format(node_count)
    config_error_text_1 = 'having required number of cells ({0})'.format(cell_count)
    config_error_text_2 = 'could not be found'
    config_error_text = '{0} {1} {2}'.format(config_error_text_0, config_error_text_1, config_error_text_2)

    return config_error_text


def get_list_of_poids_in_network(user):
    """
    Fetch all SubNetwork poids in network

    :param user: `lib.enm_user_2.User` instance
    :type user: enm_user_2.User
    :return: all subnetwork poids
    :rtype: list
    """
    poids_data = []

    response = user.get(NETWORK_PO_IDS_URL, headers=JSON_SECURITY_REQUEST)
    raise_for_status(response, message_prefix="GET response returned is NOK: ")

    res_po = response.json()
    if 'treeNodes' in res_po:
        for res in res_po['treeNodes']:
            if 'poId' in res:
                poids_data.append(res['poId'])

    return poids_data


def log_and_truncate_json_response(json_data, operation):
    """
    Logs, and truncates if necessary, the json data to be sent to the ENM service

    :param json_data: Dictionary to be sent as json to ENM REST endpoint
    :type json_data: dict
    :param operation: The operation to be performed by the cell management application
    :type operation: str
    """
    log_message = ("The {0} operation is being performed on the Cell Mgt Service with the following data:"
                   .format(operation))
    if len(json.dumps(json_data)) > 5000:
        log.logger.debug("{0}: {1} ... {2}".format(log_message, json.dumps(json_data)[0:200],
                                                   json.dumps(json_data)[-200:]))
    else:
        log.logger.debug("{0}: {1}".format(log_message, json.dumps(json_data)))


def read_cells_for_specified_poid_list_via_cell_mgt(user, poids_data):
    """
    Perform readCells on Cell Management Northbound REST interface to fetch list of cell FDN's that exist on nodes
    that are included in provided list of NetworkElement FDN's.

    :param user: `lib.enm_user_2.User` instance
    :type user: enm_user_2.User
    :param poids_data: List of subnetwork or nodes poids
    :type poids_data: list
    :return: list of cells that exist for provided NetworkElement FDN's
    :rtype: list
    """
    operation = "readCells"
    json_data = {
        "name": operation,
        "poIds": poids_data}
    log_and_truncate_json_response(json_data, operation)

    # Perform POST operation on Cell Mgt Service
    response = user.post(CELL_URL, data=json.dumps(json_data), headers=JSON_SECURITY_REQUEST)
    raise_for_status(response, message_prefix="POST response returned is NOK: ")

    return response


def extract_cell_fdns(successful_mo_operations_data, standard=None, cell_type=None):
    """
    Parse the supplied dictionary, extracting any cell fdns

    :param successful_mo_operations_data: Dict created from the readCells response object
    :type successful_mo_operations_data: dict
    :param standard: Communications standard to use
    :type standard: str
    :param cell_type: Type of cell to filter
    :type cell_type: str

    :return: List of cell fdns
    :rtype: list
    """
    standard = standard or "LTE"
    cell_type = cell_type or "EUtranCell"
    list_of_cell_lists = []
    if standard in successful_mo_operations_data:
        for cell_data in successful_mo_operations_data[standard]:
            if 'cell' in cell_data:
                list_of_cell_lists.append(filter_cells_on_cell_type([cell_data['cell']], cell_type))
            else:
                log.logger.debug("The response to the HTTP request doesnt contain expected information (cells)")
    return list_of_cell_lists


def filter_cells_on_cell_type(cells, cell_type):
    """
    Filter the list of cells by specific cell

    :param cells: List of cells to be filtered
    :type cells: list
    :param cell_type: Type of cell to filter
    :type cell_type: str

    :return: List of cell fdns
    :rtype: list
    """
    filtered_cells = []
    for cell in cells:
        if cell_type in cell.encode('utf-8'):
            filtered_cells.append(cell)
    return filtered_cells


def fetch_cell_fdns_for_specified_poid_list_via_cell_mgt(user, poids_data, standard=None, cell_type=None):
    """
    Perform readCells on Cell Management Northbound REST interface to fetch list of cell FDN's that exist on nodes
    that are included in provided list of NetworkElement FDN's.

    :param user: `lib.enm_user_2.User` instance
    :type user: enm_user_2.User
    :param poids_data: List of subnetwork or nodes poids
    :type poids_data: list
    :param standard: Technology standard to use
    :type standard: str
    :param cell_type: Type of cell to be returned
    :type cell_type: str

    :return: list of cells that exist for provided NetworkElement FDN's
    :rtype: list
    """
    standard = standard or "LTE"
    cell_type = cell_type or "EUtranCell"
    list_of_cells = []

    # Perform POST operation on Cell Mgt Service
    start = timestamp.get_current_time()
    response = read_cells_for_specified_poid_list_via_cell_mgt(user, poids_data)

    finish = timestamp.get_current_time() - start

    time_taken = timestamp.get_string_elapsed_time(finish)
    response_as_map = {}
    try:
        response_as_map = response.json()
    except Exception as e:
        log.logger.debug("The response to the HTTP request doesnt contain expected information "
                         "response: {0}".format(str(e)))

    if 'successfulMoOperations' in response_as_map.keys():
        successful_mo_operations_data = response_as_map['successfulMoOperations']
        log.logger.debug(
            'Reading of Cell Topology took {time_taken}s while reading {number_of_nodes} poIds'.format(
                time_taken=time_taken,
                number_of_nodes=len(poids_data)))

        list_of_cell_lists = extract_cell_fdns(successful_mo_operations_data, standard, cell_type)
        for each_list in list_of_cell_lists:
            list_of_cells += each_list

        log.logger.debug("Number of cells returned in REST response: {}".format(len(list_of_cells)))
    else:
        log.logger.debug("The response to the HTTP request doesnt contain expected information "
                         "(successfulMoOperations)")

    return list_of_cells


def create_list_of_node_poids(user, nodes):
    """
    Create list of node PO IDs

    :param user: `lib.enm_user_2.User` instance
    :type user: enm_user_2.User
    :param nodes: List of Nodes
    :type nodes: list
    :return: list of nodes poids
    :rtype: list
    """
    return [node.poid for node in filter_nodes_having_poid_set(nodes)]


def fetch_cell_attrs_for_spec_cell_fdn_list_via_cell_mgt(user, cell_fdn_list, standard=None):
    """
    Perform readCellData on Cell Management Northbound REST interface to fetch cell attribute data for provided
    Cell FDN's.

    :param user: `lib.enm_user_2.User` instance
    :type user: enm_user_2.User
    :param cell_fdn_list: List of NetworkElement MO's
    :type cell_fdn_list: list
    :param standard: Technology standard to use
    :type standard: str

    :raises EnmApplicationError: raised if no JSON to decode from ENM request

    :return: dictionary of cells and corresponding attributes
    :rtype: dict
    """
    standard = standard or "LTE"
    operation = "readCellsData"

    json_data = {
        "name": operation,
        "fdns": cell_fdn_list}
    log_and_truncate_json_response(json_data, operation)

    # Perform POST operation on Cell Mgt Service
    start = timestamp.get_current_time()

    response = user.post(CELL_URL, data=json.dumps(json_data), headers=JSON_SECURITY_REQUEST)
    raise_for_status(response, message_prefix="POST response returned is NOK: ")

    finish = timestamp.get_current_time() - start

    time_taken = timestamp.get_string_elapsed_time(finish)
    try:
        response_as_map = response.json()
    except ValueError as e:
        log.logger.debug(str(e))
        raise EnmApplicationError("ENM request failed, No JSON to decode. Response status code: [{0}].".format(
            response.status_code))

    cell_attribute_data = {}

    if 'successfulMoOperations' in response_as_map.keys():
        successful_mo_operations_data = response_as_map['successfulMoOperations']
        log.logger.debug(
            'Reading of Cell Data took {time_taken}s while reading {number_of_nodes} nodes'.format(
                time_taken=time_taken,
                number_of_nodes=len(cell_fdn_list)))

        if standard in successful_mo_operations_data:
            for cell_data in successful_mo_operations_data[standard]:
                cell_attribute_data.update(filter_attributes(cell_data, cell_attribute_data))
        else:
            log.logger.debug("The response to the HTTP request doesnt contain expected information (fdn)")
            return

        log.logger.debug("Number of Cells returned in REST response: {}".format(len(cell_attribute_data.keys())))
    else:
        log.logger.debug("The response to the HTTP request doesnt contain expected information "
                         "(successfulMoOperations)")

    return cell_attribute_data


def filter_attributes(cell_data, cell_attribute_data):
    """
    Filter the supplied cell data, returning the data

    :param cell_data: Cell data retrieved from ENM
    :type cell_data: dict
    :param cell_attribute_data: dictionary container for cell data
    :type cell_attribute_data: dict

    :return: Updated dictionary
    :rtype: dict
    """
    if 'fdn' in cell_data:
        cell_name = str(get_cell_name(cell_data['fdn']))
        if 'attributes' in cell_data.keys():
            cell_attribute_data[cell_name] = cell_data['attributes']
        else:
            log.logger.debug("The response to the HTTP request doesnt contain expected information "
                             "(attributes)")
    return cell_attribute_data


def read_cell_data_ui_flow(user_node_data, sleep_time, ui_display_limit=50, standard=None, cell_type=None):
    """
    Method to perform the flow of actions as typically carried out via the UI

    Based on guidance from Cell Management Design, the use case flow is similar to the following actions as carried
    out by an ENM user:

        - User X selects a SubNetwork in the UI with 500 nodes beneath it.
        - UI will send a request to the NBI to read all cells (FDNs only) for the 500 nodes
        - Assuming 1000 cell FDNs are returned, the UI will select the first 50 cell FDNs and send a second request
            to read cell data (attributes etc.) for these cells only. This is because the UI cannot obviously
            display data for all 1000 cells at once, and for performance reasons it makes no sense to fetch the data
            to be displayed till its needed (when user scrolls).
        - After 2 minutes we are suggestion that each user send the request to read the cell data for the subset of
            50 cells again. This is to simulate a user doing a refresh on the UI table that is displaying the cell
            data.

    :param user_node_data: dictionary of user and node_fdn_list
    :type user_node_data: dict
    :param ui_display_limit: integer to indicate the limit on data returned via the UI
    :type ui_display_limit: int
    :param sleep_time: integer to indicate time in seconds
    :type sleep_time: int
    :param standard: Technology standard to use
    :type standard: str
    :param cell_type: Type of cell to be returned
    :type cell_type: str

    :return: status of the ui flow
    :rtype: bool
    """

    task_completed_count = 0
    user, node_fdn_list = user_node_data

    username = user.username

    log.logger.debug("Read Cell Data UI Flow for user: {} - started".format(username))

    log.logger.debug("{0}: Task 1. 'Fetch Cell FDN's for specified list of Node FDN's ({1})".format(username,
                                                                                                    len(node_fdn_list)))
    cell_fdn_list = fetch_cell_fdns_for_specified_poid_list_via_cell_mgt(user, node_fdn_list, standard=standard,
                                                                         cell_type=cell_type)

    if cell_fdn_list:
        task_completed_count += 1

        log.logger.debug("{0}: Number of Cell FDN's received from ENM: {1}".format(username, len(cell_fdn_list)))

        selected_cell_fdns = cell_fdn_list[0:ui_display_limit]

        log.logger.debug("{0}: Task 2. Fetch Attributes for selected cell FDN's ({1}) - actual count: {2}"
                         .format(username, ui_display_limit, len(selected_cell_fdns)))
        if fetch_and_display_attribute_values(user, selected_cell_fdns, standard=standard) > 0:
            task_completed_count += 1

        log.logger.debug("{0}: Task 3. Sleeping for {1}s before re-read of data".format(username, sleep_time))
        time.sleep(sleep_time)

        log.logger.debug("{0}: Task 4. Re-fetching Attributes for selected cell FDN's ({1}) "
                         "to simulate UI refresh".format(username, ui_display_limit))
        if fetch_and_display_attribute_values(user, selected_cell_fdns, standard=standard) > 0:
            task_completed_count += 1

    if task_completed_count == 3:
        message = "All"
        flow_status = True
    else:
        message = "Not all"
        flow_status = False

    log.logger.debug("Read Cell Data UI Flow for user: {0} - {1} tasks were completed".format(username, message))

    return flow_status


def fetch_and_display_attribute_values(user, selected_cell_fdns, standard=None):
    """
    Method to fetch Call attribute data from ENM and display/log attributes for each cell

    :param user: `lib.enm_user_2.User` instance
    :type user: enm_user_2.User
    :param selected_cell_fdns: list of selected Cell FDN's
    :type selected_cell_fdns: list
    :param standard: Technology standard to use
    :type standard: str

    :return: cell_counter: integer to indicate the number of cell returned from ENM
    :rtype: int
    :raises EnvironError: raises if cell attribute data is empty
    """
    standard = standard or "LTE"
    cell_attribute_data = fetch_cell_attrs_for_spec_cell_fdn_list_via_cell_mgt(user, selected_cell_fdns,
                                                                               standard=standard)

    cell_counter = 0
    if cell_attribute_data:
        for cell_name in cell_attribute_data:
            cell_counter += 1
            log.logger.debug("{0}: Cell {1} attributes: {2}".format(cell_counter, cell_name,
                                                                    cell_attribute_data[cell_name]))
    else:
        raise EnvironError("{0}: Empty cell attribute data returned from ENM".format(user.username))

    return cell_counter


def lock_unlock_cells_flow(user_node_data, sleep_time, maximum_number_of_cells=None, standard=None, cell_type=None,
                           remove_reserved_gerancells=False):
    """
    Method that contains the tasks that make up the flow for the lock/unlock use case

    :param user_node_data: tuple containing user and node objects
    :type user_node_data: tuple
    :param sleep_time: integer to be used to delay the sending of repeat NBI request
    :type sleep_time: int
    :param maximum_number_of_cells: Limit the operation to a maximum number of cells
    :type maximum_number_of_cells: int
    :param standard: Technology standard to use
    :type standard: str
    :param cell_type: Type of cell to be returned
    :type cell_type: str
    :param remove_reserved_gerancells: Flag to remove reserved GeranCell range
    :type remove_reserved_gerancells: bool

    :return: boolean to indicate success or failure of the flow
    :rtype: bool
    """

    task_success_count = 0

    user, node_poid = user_node_data
    node_poid = [node_poid]

    username = user.username
    log.logger.debug("Lock/Unlock Cells Flow for user: {0} on node: {1} - started".format(username, node_poid))

    log.logger.debug("{0}: Task 1. 'Fetch Cell FDN's for Node: {1}".format(username, node_poid))
    cell_fdn_list = fetch_cell_fdns_for_specified_poid_list_via_cell_mgt(user, node_poid, standard=standard,
                                                                         cell_type=cell_type)
    attribute = "state" if standard == "GSM" else None
    lock_value = "HALTED" if standard == "GSM" else "LOCKED"
    unlock_value = "ACTIVE" if standard == "GSM" else "UNLOCKED"
    if cell_fdn_list:
        if remove_reserved_gerancells:
            cell_fdn_list = remove_gerancell_in_range(cell_fdn_list)
        if maximum_number_of_cells:
            cell_fdn_list = cell_fdn_list[:maximum_number_of_cells]
        task_success_count += 1

        log.logger.debug("{0}: Task 2. Lock each cell on Node: {1}".format(username, node_poid))
        if False not in [lock_unlock_cell_via_cell_mgt(user, cell_fdn, lock_value, attribute=attribute) for cell_fdn
                         in cell_fdn_list]:
            task_success_count += 1

        log.logger.debug("{0}: Task 3. Sleeping for {1}s before unlocking cell".format(username, sleep_time))
        time.sleep(sleep_time)

        log.logger.debug("{0}: Task 3. Unlock each cell on Node: {1}".format(username, node_poid))
        if False not in [lock_unlock_cell_via_cell_mgt(user, cell_fdn, unlock_value, attribute=attribute) for cell_fdn
                         in cell_fdn_list]:
            task_success_count += 1

    if task_success_count == 3:
        message = "All"
        flow_status = True
    else:
        message = "Not all"
        flow_status = False

    log.logger.debug("Lock/Unlock Cells Flow for user: {0} on node: {1} - {2} tasks were completed"
                     .format(username, node_poid, message))

    return flow_status


def lock_unlock_cell_via_cell_mgt(user, cell_fdn, lock_unlock, attribute=None):
    """
    Perform modifyCellParameters on Cell Management Northbound REST interface change the lock state of the provided
    Cell FDN.

    :param user: `lib.enm_user_2.User` instance
    :type user: enm_user_2.User
    :param cell_fdn: Cell FDN
    :type cell_fdn: list
    :param lock_unlock: desired lock state
    :type lock_unlock: str
    :param attribute: Attribute to be updated to LOCK/UNLOCK
    :type attribute: str
    :return: boolean to indicate if lock status of cell corresponds with desired lock state
    :rtype: bool
    """

    attribute = attribute or "administrativeState"
    operation = "modifyCellParameters"
    cell_name = get_cell_name(cell_fdn)

    json_data = {
        "name": operation,
        "sourceFdn": cell_fdn,
        "executionMode": "EXECUTE",
        "responseLevel": "HIGH",
        "attributes": {attribute: lock_unlock}}
    log_and_truncate_json_response(json_data, operation)

    # Perform POST operation on Cell Mgt Service
    start = timestamp.get_current_time()
    response = user.post(BASE_URL, data=json.dumps(json_data), headers=JSON_SECURITY_REQUEST)
    raise_for_status(response, message_prefix="POST response returned is NOK: ")
    finish = timestamp.get_current_time() - start

    time_taken = timestamp.get_string_elapsed_time(finish)
    response_as_map = response.json()

    if 'requestResult' in response_as_map.keys():
        request_result = response_as_map['requestResult']
        log.logger.debug(
            'Locking of cell ({0}) took {1}s '.format(cell_name, time_taken))

        if request_result == "SUCCESS" or request_result == "NO_UPDATE_REQUIRED":
            log.logger.debug("{0}: Cell {1} now has {2} = {3}".format(user.username, cell_name, attribute, lock_unlock))
            return True

    else:
        log.logger.debug("The response to the HTTP request doesnt contain expected information (requestResult)")

    return False


def get_list_of_existing_cells_on_node(user, node_name, cell_mo_type):
    """
    Get a list of existing cells on a given node

    :param user: user to carry out script engine requests
    :type user: enmutils_int.lib.enm_user_2.User
    :param node_name: name of the node to query
    :type node_name: str
    :param cell_mo_type: cell type to query
    :type cell_mo_type: str
    :return: list of existing cells on the node
    :rtype: list
    """

    log.logger.debug('Getting list of existing cells on node')

    list_of_cells = []
    cmedit_get_cells_command = 'cmedit get {0} {1}'.format(node_name, cell_mo_type)
    response = user.enm_execute(cmedit_get_cells_command)

    output = response.get_output()
    match_pattern = '(^FDN\\s+:\\s+)(.*)'
    for line in output:
        if re.search(match_pattern, line):
            fdn = line.split()[-1]
            list_of_cells.append(fdn)

    return list_of_cells


def determine_existing_cells_on_list_of_nodes(user, source_cell_type, nodes):
    """
    Determine the existing cells of specified type, for the given nodes

    :param user: user to perform requests
    :type user: enmutils_int.lib.enm_user_2.User
    :param source_cell_type: cell type to query for
    :type source_cell_type: str
    :param nodes: nodes to query for existing cells
    :type nodes: list
    :return: dict of the nodes with the cells already existing on each node
    :rtype: dict
    """

    existing_cells = {}

    for selected_node_info in nodes:
        node_name = selected_node_info.node_id
        existing_cells[node_name] = get_list_of_existing_cells_on_node(user, node_name, source_cell_type)

    return existing_cells


def view_cell_relations(user_node_data, relations, random_sleep_range=0):
    """
    Method to view cell relations for a given node
    :param relations: List of the tuples containing required relation type to view.
    :type relations: list
    :param user_node_data: tuple containing user and node objects
    :type user_node_data: tuple
    :param random_sleep_range: Random sleep time maximum value.
    :type random_sleep_range: int
    """
    user, node_name = user_node_data
    sleep_time = random.uniform(0, (random_sleep_range - 4 * 60))
    log.logger.debug("Worker will sleep for {} seconds before executing".format(int(sleep_time)))
    sleep(sleep_time)

    for relation_type in relations:
        json_data = {
            "direction": relation_type[0],
            "fdns": [node_name] if not isinstance(node_name, list) else node_name,
            "name": relation_type[1],
            "rat": relation_type[2],
            "relationType": relation_type[3]
        }
        try:
            user.post(CELL_URL, data=json.dumps(json_data), headers=JSON_SECURITY_REQUEST)
        except HTTPError:
            log.logger.error('Error occurred during viewing relations for node: {0}'.format(node_name))


def get_cell_relations(user_node_data, relation_type):
    """
    Method to view and return, cell relations for a given node

    :param relation_type: Tuple containing required relation type to view.
    :type relation_type: tuple
    :param user_node_data: tuple containing user and node objects
    :type user_node_data: tuple
    :returns: Response object from ENM request
    :rtype: `http.Response`
    """
    user, node_fdns = user_node_data
    log.logger.debug("Querying ENM for cell relations.")
    json_data = {
        "direction": relation_type[0],
        "fdns": [node_fdns] if not isinstance(node_fdns, list) else node_fdns,
        "name": relation_type[1],
        "rat": relation_type[2],
        "relationType": relation_type[3]
    }

    response = user.post(CELL_URL, data=json.dumps(json_data), headers=JSON_SECURITY_REQUEST)
    log.logger.debug("Successfully queried ENM for cell relations.")
    return response


def verify_nodes_on_enm_and_return_mo_cell_fdn_dict(user, nodes, mo_types):
    """
    Method to verify nodes against enm and return full list of cells.
    :param nodes: List of Node Objects.
    :type nodes: list
    :param user: User object to perform the queries
    :type user: User
    :param mo_types: List of required MO types
    :type mo_types: list

    :return: Dictionary of cell fdns for list of nodes passed to the function
    :rtype: dict
    """
    node_fdns = {}
    for mo_type in mo_types:
        node_fdns[mo_type] = []

    nodes_verified_on_enm = filter_nodes_having_poid_set(nodes)
    if nodes_verified_on_enm:
        for node in nodes_verified_on_enm:
            for mo_type in mo_types:
                node_fdns[mo_type] += get_all_fdn_list_of_cells_on_node(user, node.node_id, mo_type)

    return node_fdns


def get_fdn_of_node_b_function(node_name, existing_cells):
    """
    Get the FDN of the ENodeBFunction or NodeBFunction MO for a particular cell FDN

    :param node_name: name of node
    :type node_name: str
    :param existing_cells: dictionary of nodes and cells existing on those nodes
    :type existing_cells: dict
    :return: fdn of the ENodeBFunction or NodeBFunction MO
    :rtype: str
    """

    for cell_fdn in existing_cells[node_name]:
        match_pattern = '(.*?)NodeBFunction=1'
        match = re.search(match_pattern, cell_fdn)
        if match:
            return match.group(0)
    log.logger.debug('No match found in the search for fdn of NodeBFunction')
    return ''


def execute_cmedit_command_to_create_new_cell(user, cmedit_command, node_name, cell_fdn):
    """
    Execute the cmedit command to create the new cell

    :param user: user to carry out the command
    :type user: enmutils_int.lib.enm_user_2.User
    :param cmedit_command: cmedit command to create the cell
    :type cmedit_command: str
    :param node_name: name of the node
    :type node_name: str
    :param cell_fdn: FDN of the new cell
    :type cell_fdn: str
    :raises ScriptEngineResponseValidationError: ScriptEngineResponseValidationError
    :return: FDN of the new cell
    :rtype: str
    """
    log.logger.debug('Executing cmedit command {0} to create the new cell'.format(cmedit_command))
    try:
        response = user.enm_execute(cmedit_command)
    except Exception as e:
        log.logger.debug(e, 'Exception caught - could not create cell on node {0}'.format(node_name))
        return

    output = '{0}'.format('.'.join([line for line in response.get_output()]))
    if '1 instance(s) updated' not in output:
        raise ScriptEngineResponseValidationError('Could not create cell on node {0}.'.format(node_name),
                                                  response.get_output())

    log.logger.debug('Cell created: {0}'.format(cell_fdn))
    log.logger.debug('Partial output to identify instances updated: {0}'.format(output[-24:]))

    return cell_fdn


def create_cells(user, source_cell_type, existing_cells, lte_cell_type):
    """
    Create cells of the specified type on nodes

    :param user: user to perform requests
    :type user: enmutils_int.lib.enm_user_2.User
    :param source_cell_type: cell type to query
    :type source_cell_type: str
    :param existing_cells: dict with the key being the node name, and the value is the cells already existing on the
                           node
    :type existing_cells: dict
    :param lte_cell_type: The LTE Cell type, one of FDD or TDD
    :type lte_cell_type: str

    :return: dictionary of the nodes and the cells newly created on the nodes
    :rtype: dict
    """

    log.logger.debug('Creating cells of type {0}'.format(source_cell_type))
    newly_created_cells = {}
    if lte_cell_type == "FDD":
        eutran_cell_attributes = ('EUtranCellFDDId={0},'
                                  'cellId={1},'
                                  'earfcnul={2},'
                                  'earfcndl={3},'
                                  'pciConflictCell=[{{cellId=0, mcc=1, mnc=1, mncLength=2, enbId=0}}],'
                                  'pciDetectingCell=[{{cellId=0, mcc=1, mnc=1, mncLength=2, enbId=0}}],'
                                  'physicalLayerCellIdGroup=0,'
                                  'physicalLayerSubCellId=0,'
                                  'tac=0')
        attribute_one = 18001
        attribute_two = 1
    else:
        eutran_cell_attributes = ('EUtranCellTDDId={0},'
                                  'cellId={1},'
                                  'earfcn={2},'
                                  'subframeAssignment={3},'
                                  'pciConflictCell=[{{cellId=0, mcc=1, mnc=1, mncLength=2, enbId=0}}],'
                                  'pciDetectingCell=[{{cellId=0, mcc=1, mnc=1, mncLength=2, enbId=0}}],'
                                  'physicalLayerCellIdGroup=0,'
                                  'physicalLayerSubCellId=0,'
                                  'tac=0')
        attribute_one = 262100
        attribute_two = 1

    cell_id_range = [0, 255]

    for node_name in existing_cells:
        fdn_of_node_b_function = get_fdn_of_node_b_function(node_name, existing_cells)
        newly_created_cells[node_name] = {}
        newly_created_cells[node_name][source_cell_type] = {}
        offset = 0
        list_of_cells = []

        for cell_name_identifier in CELLMGT_CELL_NAME_IDENTIFIERS:
            full_cell_name = '{0}-{1}'.format(node_name, cell_name_identifier)
            cell_id = cell_id_range[0] + offset
            attribute_one += offset
            attribute_two += offset if lte_cell_type == "FDD" else 1
            offset += 1

            cell_attributes = eutran_cell_attributes.format(full_cell_name, cell_id, attribute_one, attribute_two)

            cell_fdn = '{0},{1}={2}'.format(fdn_of_node_b_function, source_cell_type, full_cell_name)
            cmedit_command = 'cmedit create {cell_fdn} {cell_attributes}'.format(cell_fdn=cell_fdn,
                                                                                 cell_attributes=cell_attributes)

            new_cell = execute_cmedit_command_to_create_new_cell(user, cmedit_command, node_name, cell_fdn)
            list_of_cells.append(new_cell)

        newly_created_cells[node_name][source_cell_type] = list_of_cells

    return newly_created_cells


def execute_cmedit_command_to_delete_cells(user, cell_fdn):
    """
    Execute the cmedit command to delete all newly created cells on the cell FDN

    :param user: user to perform requests
    :type user: enmutils_int.lib.enm_user_2.User
    :param cell_fdn: FDN of the cell to delete
    :type cell_fdn: str
    :return: number of MOs deleted as a result of deleting the cell
    :rtype: list
    :raises EnvironError: if error executing cmedit command
    """

    log.logger.debug('Executing cmedit command to delete cells on cell FDN {0}'.format(cell_fdn))

    cmedit_command = 'cmedit delete {0} -ALL'.format(cell_fdn)

    try:
        response = user.enm_execute(cmedit_command)
    except Exception as e:
        raise EnvironError(e, 'Could not delete cell on ENM')

    output = response.get_output()

    log.logger.debug('Cell deleted successfully: {0}'.format(cell_fdn))
    log.logger.debug('Partial output to identify instances updated: {0}'.format(
        '.'.join([line for line in output])[-24:]))

    num_instances_deleted = 0

    for output_string in output:
        if 'instance(s)' in output_string:
            num_instances_deleted = sum([int(string) for string in output_string.split() if string.isdigit()])
            break
    log.logger.debug('Number of MOs deleted as a result of deleting cell: {0}'.format(num_instances_deleted))

    return num_instances_deleted


def delete_cells(user, newly_created_cells):
    """
    Delete cells previously created

    :param user: user to perform requests
    :type user: enmutils_int.lib.enm_user_2.User
    :param newly_created_cells: cells previously created on the node
    :type newly_created_cells: list
    :return: True if the number of instances deleted is greater than 0 else False
    :rtype: Boolean
    """

    log.logger.debug('Deleting cells')
    num_instances_deleted = 0

    for node_name in newly_created_cells:
        for source_cell_type in newly_created_cells[node_name]:
            for cell_fdn in newly_created_cells[node_name][source_cell_type]:
                num_instances_deleted = execute_cmedit_command_to_delete_cells(user, cell_fdn)

    return True if num_instances_deleted > 0 else False


def create_flow(user_node_tuple, profile, relation_type):
    """
    Execute a series of create operations

    :param user_node_tuple: Tuple containing user object, source and target fdns
    :type user_node_tuple: tuple
    :param profile: Profile to add the exception to
    :type profile: `lib.profile.Profile`
    :param relation_type: Type of relation to be created
    :type relation_type: str
    """
    log.logger.debug("Starting create flow.")
    user, source_target_tuple = user_node_tuple
    source_node_fdns, target_node_fdns = source_target_tuple
    for source_node_fdn, target_node_fdn in zip(source_node_fdns, target_node_fdns):
        try:
            created_relation = create_external_cell_relation(user, source_node_fdn, target_node_fdn, relation_type)
            if created_relation:
                profile.RELATIONS_TO_DELETE.append(created_relation)
            else:
                log.logger.debug("Issue creating relation for {0}. "
                                 "Profile will clean up relations at end of iteration".format(source_node_fdn))
                profile.FAILED_CREATES.append(source_node_fdn)
        except Exception as e:
            profile.add_error_as_exception(e)
            profile.FAILED_CREATES.append(source_node_fdn)
    log.logger.debug(
        "\n{0}/{1} relations successfully created.".format(len(profile.RELATIONS_TO_DELETE), len(source_node_fdns)))
    log.logger.debug("Completed create flow.")


def delete_flow(user_node_tuple, profile):
    """
    Execute a series of delete operations

    :param user_node_tuple: Tuple containing user object, source and target fdns
    :type user_node_tuple: tuple
    :param profile: Profile to add the exception to
    :type profile: `lib.profile.Profile`
    """
    log.logger.debug("Starting delete flow.")
    user, source_node_fdns = user_node_tuple
    for source_node_fdn in source_node_fdns:
        log.logger.debug("\nDeleting relation from source: {0}\n.".format(source_node_fdn))
        try:
            delete_cell_relation(user, source_node_fdn)
        except Exception as e:
            profile.add_error_as_exception(e)
    log.logger.debug("Completed delete flow.")


def create_external_cell_relation(user, source_node_fdn, target_node_fdn_data, relation_to_create):
    """
    Create a cell relation via cell management REST endpoint

    :param user: User object to perform the creation
    :type user: `enm_user_2.User`
    :param source_node_fdn: FDN(s) of the source to create relation between
    :type source_node_fdn: str
    :param target_node_fdn_data: Target node data to create relation between
    :type target_node_fdn_data: dict
    :param relation_to_create: Type of relation to be created, for example: ExternalGeranCellRelation
    :type relation_to_create: str

    :returns: The FDN of the created Relation
    :rtype: str
    """
    log.logger.debug("Sending create {0} request for {1}".format(relation_to_create, source_node_fdn))
    json_data = {
        "executionMode": "EXECUTE",
        "responseLevel": "HIGH",
        "name": "createRelation",
        "sourceFdn": source_node_fdn,
        "relationType": relation_to_create,
    }
    json_data.update(target_node_fdn_data)
    response = user.post(BASE_URL, data=json.dumps(json_data), headers=JSON_SECURITY_REQUEST)
    raise_for_status(response, message_prefix="POST response returned is NOK: ")
    successful_mos_operations = response.json().get('successfulMoOperations')
    relation_fdn = None
    if successful_mos_operations:
        fdns = [operation.get('fdn') for operation in successful_mos_operations]
        relation_fdn = [fdn for fdn in fdns if relation_to_create in fdn]
        relation_fdn = relation_fdn[0] if relation_fdn else None
    msg = ("Successfully created cell relation: {0}".format(relation_fdn)
           if relation_fdn else "Cell relation did not create successfully, response: [{0}].".format(response.json()))
    log.logger.debug(msg)
    return relation_fdn


def delete_cell_relation(user, source_node_fdn):
    """
    Delete a cell relation via cell management REST endpoint

    :param user: User object to perform the deletion
    :type user: `enm_user_2.User`
    :param source_node_fdn: FDN(s) of the source node to delete fromcme
    :type source_node_fdn: str
    """
    log.logger.debug("Sending delete cell relation request.")
    json_data = {
        "executionMode": "EXECUTE",
        "responseLevel": "HIGH",
        "name": "deleteRelation",
        "sourceFdn": source_node_fdn
    }
    response = user.post(BASE_URL, data=json.dumps(json_data), headers=JSON_SECURITY_REQUEST)
    # The default behaviour is to attempt to delete every possibly created relation
    if not response or not response.text:
        log.logger.debug("ENM service failed to return a valid response, unable to determine deletion status.")
        return
    if response.json() and response.json().get(
            "requestErrorMessage") and "Invalid or non existing" in response.json().get("requestErrorMessage"):
        log.logger.debug("FDN invalid or not found, nothing to delete.")
        return
    raise_for_status(response, message_prefix="POST response returned is NOK: ")
    if response.json() and response.json().get("requestResult") in ["ERROR", "Error"]:
        log.logger.debug("Failed to delete cell relation correctly.\nRequest made: \t[{0}]\nResponse: \t[{1}]"
                         .format(json.dumps(json_data), response.json()))
    log.logger.debug("Successfully deleted cell relation.")


def delete_cell_via_rest(user, target_fdn, force=True):
    """
    Delete a cell via cell management REST endpoint.

    :param user: user object.
    :type user: enmutils.lib.enm_user_2.User.
    :param target_fdn: FDN of cell to be deleted.
    :type target_fdn: str
    :param force: Use the force option to delete a cell along with its outgoing and incoming cell
    relations and frequency relations.
    :type force: bool
    """
    log.logger.debug("Attempting to delete cell. Force={0}".format(force))
    json_data = {
        "executionMode": "EXECUTE",
        "responseLevel": "HIGH",
        "name": "deleteCell",
        "fdn": target_fdn,
        "force": "true" if force else 'false'
    }

    response = user.post(BASE_URL, data=json.dumps(json_data), headers=JSON_SECURITY_REQUEST)
    raise_for_status(response, message_prefix="POST response returned is NOK: ")
    if response.json() and response.json().get("requestResult") in ["ERROR", "Error"]:
        log.logger.debug("Cell failed to delete cell correctly.\nRequest made: \t[{0}]\nResponse: \t[{1}]"
                         .format(json.dumps(json_data), response.json()))
    else:
        log.logger.debug("Successfully deleted cell: {0}".format(target_fdn))


def create_utran_attributes(cell_id, target_fdn):
    """
    Generates attributes dict for UtranCell creation.

    :param target_fdn: Base FDN used to generate iubLinkRef.
    :type target_fdn: str
    :param cell_id: Cell Id.
    :type cell_id: str
    :return: Attributes dict for UtranCell creation.
    :rtype: dict
    """

    return {
        "UtranCell": {
            "cId": cell_id,
            "localCellId": cell_id,
            "primaryScramblingCode": "0",
            "sib1PlmnScopeValueTag": "0",
            "tCell": "0",
            "uarfcnDl": "10",
            "uarfcnUl": "10",
            "iubLinkRef": "{0},IubLink=1".format(target_fdn.split(',UtranCell')[0])
        },
        "LocationArea": {
            "lac": "1"},
        "ServiceArea": {
            "sac": "1"}
    }


def create_eutran_attributes(target_fdn, lte_cell_type):
    """
    Generates attributes dict for EUtranCell creation.

    :param target_fdn: FDN of of cell to be created.
    :type target_fdn: str
    :param lte_cell_type: The LTE Cell type, one of FDD or TDD
    :type lte_cell_type: str
    :return: Attributes dict for EUtranCell creation.
    :rtype: dict
    :raises EnvironError: if type of lte_cell_type is not unicode

    """
    if isinstance(lte_cell_type, unicode):
        eutrancellfddid = ("eUtranCellFDDId".replace("FDD", lte_cell_type) if 'dg2' in target_fdn else
                           "EUtranCellFDDId".replace("FDD", lte_cell_type))
    else:
        raise EnvironError("Type of lte_cell_type is not a unicode")

    if lte_cell_type == "FDD":
        return {
            "EUtranCellFDD": {
                "cellId": target_fdn.split('-')[-1],
                eutrancellfddid: target_fdn.split('=')[-1],
                "physicalLayerCellIdGroup": "1",
                "physicalLayerSubCellId": "1",
                "tac": "1",
                "earfcndl": "2",
                "earfcnul": "18002"}
        }
    else:
        return {
            "EUtranCellTDD": {
                "cellId": target_fdn.split('-')[-1],
                eutrancellfddid: target_fdn.split('=')[-1],
                "physicalLayerCellIdGroup": "1",
                "physicalLayerSubCellId": "1",
                "tac": "1",
                "subframeAssignment": "1",
                "earfcn": "262100"}
        }


def build_create_cell_json(target_fdn, cell_type, cell_id, lte_cell_type):
    """
    Builds json needed for cell create request.

    :param target_fdn: FDN of cell to be created.
    :type target_fdn: str
    :param cell_type: Type of cell to be created.
    :type cell_type: str
    :param cell_id: Id given to cell
    :type cell_id: str
    :param lte_cell_type: The LTE Cell type, one of FDD or TDD
    :type lte_cell_type: str

    :return: dict containing json data
    :rtype: dict
    """

    json_data = {
        "executionMode": "EXECUTE",
        "responseLevel": "HIGH",
        "name": "createCell",
        "fdn": target_fdn,
        "attributes": (create_utran_attributes(cell_id, target_fdn) if cell_type == "UtranCell" else
                       create_eutran_attributes(target_fdn, lte_cell_type))
    }

    return json_data


def generate_cell_id_for_utrancell(profile, user, node_name):
    """
    Generate cell id for the Utrancell to be created.
    Same cell id should not be preferably present for another cell of the same node.

    :param profile: Profile object.
    :type profile: 'profile.Profile'
    :param user: User object to perform cell creation.
    :type user: `enm_user_2.User`
    :param node_name: Node name
    :type node_name: str

    :return: cell id for the cell to be created
    :rtype: int
    """
    log.logger.debug("Attempting to generate cell id for Utrancell to be created.")
    new_cell_id = random.randrange(*UTRAN_CID_RANGE)
    try:
        response = user.enm_execute("cmedit get {0} UtranCell.cId".format(node_name))
        output = response.get_output()
        existing_cell_ids = [int(line.split("cId : ")[1]) for line in output if "cId" in line]
        new_cell_id = tuple(set(range(*UTRAN_CID_RANGE)) - set(existing_cell_ids))[0]
    except Exception as e:
        log.logger.debug("Please check whether the command to get cId gives output in a proper format.")
        profile.add_error_as_exception(EnmApplicationError(e))
    log.logger.debug("Completed attempt to generate cell id for Utrancell to be created. New cell id - {0}.".format(new_cell_id))
    return new_cell_id


def create_cell_via_rest(user, profile, target_fdns, cell_type, lte_cell_type, node_name=None):
    """
    Creates a cell for each FDN in target_fdns.

    :param user: User object to perform cell creation.
    :type user: `enm_user_2.User`
    :param profile: Profile object.
    :type profile: 'profile.Profile'
    :param target_fdns: List of new cell FDNs.
    :type target_fdns: list
    :param cell_type: Type of cell to be created.
    :type cell_type: str
    :param lte_cell_type: The LTE Cell type, one of FDD or TDD
    :type lte_cell_type: str
    :param node_name: Node name
    :type node_name: str

    :return: Tuple containing a list of created cells and a dict of failed cells with error messages.
    :rtype: tuple
    """

    created_cells = []
    failed_cells = {}
    cell_id = 0

    log.logger.debug("Attempting to create {0} cell(s).".format(len(target_fdns)))
    for fdn in target_fdns:
        try:
            if cell_type != "UtranCell":
                cell_id += 1
            else:
                cell_id = generate_cell_id_for_utrancell(profile, user, node_name)
            json_data = build_create_cell_json(fdn, cell_type, str(cell_id), lte_cell_type)
            log.logger.debug("Attempting to create cell: {0}\tJSON\t{1}\n.".format(fdn, json_data))
            response = user.post(BASE_URL, data=json.dumps(json_data), headers=JSON_SECURITY_REQUEST)
            raise_for_status(response, message_prefix="POST response returned is NOK: ")
            log.logger.debug("Successfully created cell: {}".format(fdn))
            created_cells.append(fdn)
        except HTTPError as e:
            profile.add_error_as_exception(e)
            failed_cells[fdn] = e.message
    log.logger.debug("Created {0}/{1} cell(s) of type '{cell_type}'.".format(len(created_cells),
                                                                             len(target_fdns), cell_type=cell_type))

    return created_cells, failed_cells


def read_cells_network_element(user, network_element, standard, cell_type):
    """
    Retrieves a list of cells of type cell_type for the specified network_element.

    :param user: User object to perform readCell request.
    :type user: `enm_user_2.User`
    :param network_element: Name of NetworkElement.
    :type network_element: str
    :param standard: Cell standard. Response filtered on standard.
    :type standard: str
    :param cell_type: Filter response for given cell type.
    :type cell_type: str
    :return: List of cells of cell_type.
    :rtype: list
    """

    json_data = {
        'name': 'readCells',
        'fdn': "NetworkElement={0}".format(network_element)
    }
    cell_fdns = []
    response_as_map = {}

    log.logger.debug("Performing readCells for NetworkElement={0}".format(network_element))
    try:
        response = user.post(CELL_URL, data=json.dumps(json_data), headers=JSON_SECURITY_REQUEST)
        raise_for_status(response, message_prefix="POST response returned is NOK: ")
        response_as_map = response.json()
    except Exception as e:
        log.logger.debug('Error occurred retrieving cell relations: {0}'.format(str(e)))
    if 'successfulMoOperations' in response_as_map.keys():
        successful_mo_operations_data = response_as_map['successfulMoOperations']
        log.logger.debug("Filtering cells for cell type : {0}".format(cell_type))
        cell_fdns = extract_cell_fdns(successful_mo_operations_data, standard, cell_type)

    return cell_fdns


def get_utran_network(user, node_name):
    """
    Gets all UtranNetwork FDNs for the given node.
    :param user: user to perform query
    :type user: enm_user_2.User
    :param node_name: Node name
    :type node_name: str
    :return: List of UtranNetwork FDNs.
    :rtype: list
    :raises Exception: raises if user.enm_execute fails
    :raises EnmApplicationError: raises if no UtranNetwork FDNs are returned by cmedit command.
    """

    utran_network_fdns = []
    cmd = "cmedit get {0} UtranNetwork".format(node_name)
    response = user.enm_execute(cmd)

    output = response.get_output()
    match_pattern = '(^FDN\\s+:\\s+)(.*)'
    for line in output:
        if re.search(match_pattern, line):
            fdn = line.split()[-1]
            utran_network_fdns.append(fdn)
    if not utran_network_fdns:
        raise EnmApplicationError('No UtranNetwork FDNs in cmedit response: {0}'.format(output))

    return utran_network_fdns


def create_geran_freq_group_relation(user, source_fdn, freq_group_id, frequencies):
    """
    Creates a GeranFreqGroupRelaion under the provided source FDN.
    :param user: User to make request.
    :type user: `enm_user_2.User`
    :param source_fdn: FDN of source cell.
    :type source_fdn: str
    :param freq_group_id: Id to reference GeranFreqGroup under GeraNetwork.
    :type freq_group_id: int
    :param frequencies: Frequencies to reference GeranFrequecies under GeraNetwork.
    :type frequencies: list
    :return: FDN of created GeranFreqGroupRelation.
    :rtype: str
    """
    relation_type = "GeranFreqGroupRelation"
    json_data = {
        "frequencyGroupId": freq_group_id,
        "frequencies": frequencies,
        "bandIndicator": "PCS_1900"
    }

    return create_external_cell_relation(user, source_fdn, json_data, relation_type)


class IurLink(object):
    EXISTING_IURLINK_CMD = "cmedit get {rnc_function},IurLink={profile_name}-{rnc_id}"
    CREATE_IURLINK_CMD = ("cmedit create {rnc_function},IurLink={profile_name}-{rnc_id} "
                          "utranNetworkRef='{utran_network_fdn}';"
                          "IurLinkId={profile_name}-{rnc_id};"
                          "rncId={rnc_id};"
                          "userPlaneTransportOption={{ipv4=TRUE, atm=FALSE}}")

    def __init__(self, profile, user, rnc_function, rnc_id, utran_network_fdn):
        """
        Init method.
        :param profile: Profile object.
        :type profile: enmutils_int.lib.profile.Profile
        :param user: User object.
        :type user: enm_user_2.User
        :param rnc_function: RncFunction FDN of source Rnc.
        :type rnc_function: str
        :param rnc_id: RncId of destination Rnc.
        :type rnc_id: int
        :param utran_network_fdn: UtranNetwork FDN of source Rnc.
        :type utran_network_fdn: str
        """

        self.profile = profile
        self.user = user
        self.rnc_function = rnc_function
        self.rnc_id = rnc_id
        self.utran_network_fdn = utran_network_fdn
        self._iurlink_exists = False

    @property
    def iurlink_exists(self):
        return self._iurlink_exists

    def execute(self):
        """
        Executes IurLink checking and creating flow.
        """
        try:
            self.check_if_iurlink_exists()
            if not self.iurlink_exists:
                self.create_iurlink()
        except Exception as e:
            self.profile.add_error_as_exception(e)

    def check_if_iurlink_exists(self):
        """
        Checks for existing IurLink between two RNCs.
        """

        cmd = self.EXISTING_IURLINK_CMD.format(rnc_function=self.rnc_function,
                                               profile_name=self.profile.NAME,
                                               rnc_id=self.rnc_id)

        log.logger.debug("Checking if IurLink exists from {0} to RNC with Id {1}".format(self.rnc_function,
                                                                                         self.rnc_id))
        try:
            response = self.user.enm_execute(cmd)
            if str(response.get_output()[-1]).split(' ')[0] == "1":
                log.logger.debug("IurLink already exists for {0} to RNC with Id {1}".format(self.rnc_function,
                                                                                            self.rnc_id))
                self._iurlink_exists = True
            elif str(response.get_output()[-1]).split(' ')[0] == "0":
                log.logger.debug("IurLink does not already exist for {0} to RNC with Id {1}.".format(self.rnc_function,
                                                                                                     self.rnc_id))
                self._iurlink_exists = False
            else:
                raise ScriptEngineResponseValidationError(" . ".join(response.get_output()), response)

        except Exception as e:
            log.logger.debug('Could not determine if IurLink already exists. Error: {0}.'.format(e.message))
            raise e

    def create_iurlink(self):
        """
        Creates an IurLink between two RNCs.
        """

        cmd = self.CREATE_IURLINK_CMD.format(rnc_function=self.rnc_function,
                                             profile_name=self.profile.NAME,
                                             rnc_id=self.rnc_id,
                                             utran_network_fdn=self.utran_network_fdn)
        try:
            response = self.user.enm_execute(cmd)
            if str(response.get_output()[-1]) in "1 instance(s) updated":
                log.logger.debug("IurLink successfully created for {0} to RNC with Id {1}".format(self.rnc_function,
                                                                                                  self.rnc_id))
                self._iurlink_exists = True
            else:
                raise ScriptEngineResponseValidationError("IurLink not created: {0}".format(response.get_output()),
                                                          response)

        except Exception as e:
            log.logger.debug(
                "Error: IurLink for {0} to RNC with Id {1}: {2}".format(self.rnc_function, self.rnc_id, e.message))
            self._iurlink_exists = False
            raise e
