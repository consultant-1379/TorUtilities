# ********************************************************************
# Name    : CMCLI
# Summary : Primary module used by ENMCLI profiles.
#           Allows the user to retrieves a number of URIs, or execute
#           and evaluate ENM CLI commands.
# ********************************************************************

import re
import random

from retrying import retry

from enmutils.lib import log
from enmutils.lib.exceptions import ScriptEngineResponseValidationError, EnvironError, EnmApplicationError

HEADERS = {'Content-Type': 'application/json; charset=utf-8'}
GET_CELLS_ON_NODE = "cmedit get {node_id} {cell_type}.{cell_id}"
GET_GERANCELL_ON_NODE = "cmedit get {node_id} GeranCell"
GET_CELL_ADMIN_STATE = "cmedit get {node_id} {cell_type}.administrativeState"
SET_CELL_ADMIN_STATE = "cmedit set {node_id} EUtranCellFDD administrativeState={state}"
GET_CELLS_RELATIONS = "cmedit get {node_id} {cell_type}, {relation_type}"
GET_COLLECTION = "collection get {collection_name}"
GET_CELL_ATTRIBUTE = "cmedit get {node_id} {cell_type}.{cell_type}Id=={cell_id} {cell_type}.({attribute})"
SET_CELL_ATTRIBUTE = "cmedit set {node_id} {cell_type}.{cell_type}Id=={cell_id} {cell_type}.{attribute}={value}"
GET_NETWORK_SYNC_STATUS = "cmedit get * CmFunction.syncStatus"
LIST_OBJECTS_WITH_SPECIFIC_VALUES = "cmedit get * {node_function},{cell_type}.(administrativeState==LOCKED)"
GET_BFD = "cmedit get * BFD.ipNetwork"
GET_CELLS_CDMA20001 = None
GET_CELLS_ZZZTEMPORARY34 = "cmedit get {node_id} {cell_type}.zzzTemporary34"
GET_CSIRSPERIODICITY = "cmedit get {node_id} {cell_type}.csiRsPeriodicity"
HELP_URLS = ['/#help/app/cliapp', '/#help/app/cliapp/concept/cli',
             '/#help/app/cliapp/concept/tutorials_cli/UsabilityFeatures',
             '/#help/app/cliapp/concept/tutorials_cli/AliasCommand',
             '/#help/app/cliapp/concept/tutorials_cli/BatchExecute',
             '/#help/app/cliapp/concept/tutorials_cm/EnableCMSupervision', '/#help/app/cliapp/concept/cmedit',
             '/#help/app/cliapp/concept/tutorials_cmedit/GetNodeDataByFDN',
             '/#help/app/cliapp/concept/tutorials_cmedit/GetNodeData',
             '/#help/app/cliapp/concept/tutorials_cmedit/SetNodeData']


def cm_cli_home(user):
    """
    Visit the CM CLI home page

    :type user: `enm_user_2.User`
    :param user: User who will execute the GET request
    """
    get_url_and_log_result(user, '/#cliapp')


def get_url_and_log_result(user, url):
    """
    Perform a GET request for the provided URL

    :type user: `enm_user_2.User`
    :param user: User who will execute the GET request
    :type url: str
    :param url: ENM url to request
    """
    response = user.get(url)
    if response.status_code >= 400:
        log.logger.debug("Failed to get url: {0}, status code: {1}".format(url, response.status_code))


def get_collection(user, collection):
    """
    Retrieves collection from ENM

    :type user: `enm_user_2.User`
    :param user: User who will execute the command on ENM
    :type collection: str
    :param collection: Name of the ENM collection to retrieve

    :rtype: `terminal.TerminalOutput`
    :return: Returns the enm cli response object
    """
    return execute_command_on_enm_cli(user, GET_COLLECTION.format(collection_name=collection.lower()))


def get_node_cells(user, node, cell_type):
    """
    Getting all cells on a given node

    :param user: User who will execute the command on ENM
    :type user: `enm_user_2.User`
    :param node: Node object
    :type node: `lib.enm_node.Node` instance
    :param cell_type: Target cell type
    :type cell_type: str
    :return: list of cell ids of a given node
    :rtype: list

    :raises ScriptEngineResponseValidationError: raised if no cells found on node
    """

    cell_id = cell_type + 'Id'
    response = execute_command_on_enm_cli(user, GET_CELLS_ON_NODE.format(node_id=node.node_id, cell_type=cell_type,
                                                                         cell_id=cell_id))
    output = response.get_output()[1:]

    cell_ids = []
    for c_id in [item for item in output if cell_id.lower() in item.lower()]:
        cell_ids.append(c_id.split(":")[1].strip())

    if any(re.search(r'(error)', line, re.I) for line in response.get_output()) or not cell_ids:
        raise ScriptEngineResponseValidationError(
            "ScriptEngineResponse contains zero cells in node {0}"
            "Response was {1}".format(node.node_id, ','.join(output)), response=response)

    return cell_ids


@retry(retry_on_exception=lambda e: isinstance(e, ScriptEngineResponseValidationError), wait_fixed=10000,
       stop_max_attempt_number=3)
def get_cell_relations(user, node, cell_type, relation_type=None):
    """
    Running the command to list all cell relations on a given node

    :param user: User who will execute the command on ENM
    :type user: `enm_user_2.User`
    :param node: Node object
    :type node: `lib.enm_node.Node` instance
    :param cell_type: Target cell type
    :type cell_type: str
    :param relation_type: Target cell relation
    :type relation_type: str
    """
    if not relation_type:
        relation_type_list = {cell_type: ["EUtranFreqRelation", "EUtranCellRelation"],
                              "NRCellCU": ["NRCellRelation", "NRFreqRelation"]}
        relation_type = random.choice(relation_type_list[cell_type])
    execute_command_on_enm_cli(user, GET_CELLS_RELATIONS.format(node_id=node.node_id, cell_type=cell_type,
                                                                relation_type=relation_type))


def set_cell_attributes(user, node, cell, attribute_dict, cell_type="EUtranCellFDD"):
    """
    Setting the values of all attributes in a given dictionary

    :param user: User who will execute the command on ENM
    :type user: `enm_user_2.User`
    :param node: Node object
    :type node: `lib.enm_node.Node` instance
    :param cell: a given cell on a node
    :type cell: str
    :param attribute_dict: dictionary of attribute and value pairs
    :type attribute_dict: dict
    :param cell_type: Target cell type
    :type cell_type: str

    :raises EnvironError: raised if not attribute is None type
    :raises EnvironError: raised if value of attribute is None type
    """

    for attribute, value in attribute_dict.iteritems():
        if not attribute or not value:
            if not attribute:
                raise EnvironError("Cell attributes could not be changed for node: {0} because attribute value was "
                                   "None.".format(node.node_id))
            else:
                raise EnvironError("Cell attributes could not be change for node: {0} because the attribute was "
                                   "None.".format(node.node_id))
        execute_command_on_enm_cli(user, SET_CELL_ATTRIBUTE.format(node_id=node.node_id, cell_type=cell_type,
                                                                   cell_id=cell, attribute=attribute, value=value))


@retry(retry_on_exception=lambda e: isinstance(e, ScriptEngineResponseValidationError), wait_fixed=10000,
       stop_max_attempt_number=3)
def get_cell_attributes(user, node, cell, attributes, cell_type="EUtranCellFDD"):
    """
    Getting the values of all attributes in a given dictionary

    :type user: `enm_user_2.User`
    :param user: User who will execute the command on ENM
    :type node: node
    :param node: `lib.enm_node.Node` instance
    :type cell: str
    :param cell: a given cell on a node
    :type attributes: list
    :param attributes: list of cell attributes
    :type cell_type: str
    :param cell_type: type of cell, e.g. LTE, WRAN etc

    :rtype: dict
    :return: dict of cell attributes and their values
    """
    # Combining attributes into one command reduces the need for multiple ENM queries for multiple attributes on 1 FDN
    response = execute_command_on_enm_cli(user, GET_CELL_ATTRIBUTE.format(node_id=node.node_id,
                                                                          cell_type=cell_type,
                                                                          cell_id=cell,
                                                                          attribute=','.join(attributes)))
    output = response.get_output()
    attribute_default = {}
    for attribute in attributes:
        for item in output:
            if attribute in item and ":" in item:
                attribute_default[item.split(":")[0].strip().encode('UTF-8')] = item.split(":")[1].strip().encode('UTF-8')

    return attribute_default


def cm_cli_help(user):
    """
    Browse the cm cli help page

    :type user: `enm_user_2.User`
    :param user: User who will execute the GET request
    """

    for url in HELP_URLS:
        get_url_and_log_result(user, url)


def get_administrator_state(user, node, cell_type):
    """
    Getting the cell ids and their administrator state

    :type user: `enm_user_2.User`
    :param user: User who will execute the command on ENM
    :type node: node
    :param node: `lib.enm_node.Node` instance
    :param cell_type: Target node cell type
    :type cell_type: str

    :rtype: list
    :return: list of dictionaries that store the cell ids and administrator states of each cell on a given node
    """
    response = execute_command_on_enm_cli(user, GET_CELL_ADMIN_STATE.format(node_id=node.node_id, cell_type=cell_type))
    return _process_get_administrator_state_response(response, cell_type=cell_type), response


def _process_get_administrator_state_response(response, cell_type):
    """
    Processes the output from the GET_CELL_ADMIN_STATE
    :type: script_engine_2.Response
    :param: The script_engine_2 Response object returned when the administrative state was requested

    :raises ScriptEngineResponseValidationError: If the output from the response could not be parsed as expected

    :rtype: list
    :return: list of dictionaries that store the cell ids and administrator states of each cell on a given node
    """

    output = response.get_output()
    cell_data_string = ""
    for item in output:
        if cell_type.lower() in item.lower():
            cell_data_string += "{}+".format(item.split(",")[-1].split("=")[1])
        if "administrativeState" in item:
            cell_data_string += "{}|".format(item.split(":")[1].strip())

    cell_id_and_admin_state_list = cell_data_string[:-1].split("|")
    cell_list = []
    for cell_data in cell_id_and_admin_state_list:
        cell = cell_data.split("+")
        if isinstance(cell, list) and len(cell) == 2:
            cell_list.append({"cell_id": cell[0], "cell_state": cell[1]})
        else:
            raise ScriptEngineResponseValidationError(
                "ScriptEngineResponse could not be processed correctly. "
                "Response was {0}".format(','.join(response.get_output())), response=response)
    return cell_list


def get_network_sync_status(user):
    """
    Gets the sync status of every node on the system

    :type user: `enm_user_2.User`
    :param user: User who will execute the command on ENM

    :return: Output from the sync status command
    :rtype: str
    """
    response = execute_command_on_enm_cli(user, GET_NETWORK_SYNC_STATUS)
    return _process_get_network_sync_status(response)


def _process_get_network_sync_status(response):
    """
    Returns the sync status of the network

    :param response: Response from the network sync status
    :type response: `terminal.TerminalOutput`

    :return: Network sync status
    :rtype: str
    """
    network_status = {}
    output = response.get_output()[1:]

    node_name = ''
    node_sync_status = ''
    for line in output:
        if 'NetworkElement='.lower() in line.lower():
            node_name = line.split(',')[0].split('=')[1]
        if 'syncStatus'.lower() in line.lower():
            node_sync_status = line.split(':')[1].strip()

        if all([node_sync_status, node_name]):
            network_status[node_name] = node_sync_status
            node_name = node_sync_status = ''

    return network_status


def list_objects_in_network_that_match_specific_criteria(user, node_function, cell_type):
    """
    List all objects in the network that are of a specific type and have a specific value

    :type user: `enm_user_2.User`
    :param user: User who will execute the command on ENM
    :param node_function: Node function. eg  ENodeBFunction, GNBCUCPFunction
    :type node_function: str
    :param cell_type: Cell type. eg EUtranCellFDD, EUtranCellTDD, NRCellDU
    :type cell_type: str
    :rtype: `terminal.TerminalOutput`
    :return: Returns the enm cli response object
    """
    return execute_command_on_enm_cli(user, LIST_OBJECTS_WITH_SPECIFIC_VALUES.format(node_function=node_function,
                                                                                     cell_type=cell_type))


def get_bfd(user):
    """
    Gets the BFD network on the system

    :type user: `enm_user_2.User`
    :param user: User who will execute the command on ENM
    :rtype: `terminal.TerminalOutput`
    :return: Returns the enm cli response object
    """
    return execute_command_on_enm_cli(user, GET_BFD)


def get_cells_zzztemporary34_csirsperiodicity(user, node_id, node_type='ENodeB', cell_type=None):
    """
    Gets zzzTemporary34(4G) or csirsperiodicity(5G) cells of every node on the system

    :param user: User who will execute the command on ENM
    :type user: `enm_user_2.User`
    :param node_id: Node id
    :type node_id: str
    :param node_type: Type of node to run command towards
    :type node_type: str
    :param cell_type: Cell type. eg EUtranCellFDD, EUtranCellTDD, NRCellDU
    :type cell_type: str
    :rtype: `terminal.TerminalOutput`
    :return: Returns the enm cli response object
    """
    node_id = "{0}*".format(node_id[:-2])
    if node_type == 'ENodeB':
        return execute_command_on_enm_cli(user, GET_CELLS_ZZZTEMPORARY34.format(node_id=node_id, cell_type=cell_type))
    else:
        return execute_command_on_enm_cli(user, GET_CSIRSPERIODICITY.format(node_id=node_id, cell_type=cell_type))


def execute_command_on_enm_cli(user, command, timeout=300):
    """
    Executes the provided command on ENM

    :type user: `enm_user_2.User`
    :param user: User who will execute the command on ENM
    :type command: str
    :param command: Command to be executed on ENM cli
    :type timeout: int
    :param timeout: timeout value in seconds

    :raises ScriptEngineResponseValidationError: raised when command fails to execute correctly
    :raises EnmApplicationError: raised if there is any issue in executing the command
    :rtype: `terminal.TerminalOutput`
    :return: Returns the enm cli response object
    """
    try:
        response = user.enm_execute(command, timeout_seconds=timeout)
        request_id = response._handler._last_request_id if response and response._handler else "No request id returned."
        if any(re.search(r'(error|failed)', line, re.I) for line in response.get_output()):
            raise ScriptEngineResponseValidationError("Failed to execute command: {0}, request_id: [{1}]."
                                                      "Please check ENM logviewer for more"
                                                      " information.".format(command, request_id),
                                                      response=response)
        log.logger.debug('Successfully executed command: {0} request id: [{1}]'.format(command, request_id))
        return response
    except Exception as e:
        raise EnmApplicationError(e)


def get_node_gerancell_value(users, nodes):
    """
    Getting all cells on a given node

    :type users: list
    :param users: List of Users who will execute the command on ENM
    :type nodes: list
    :param nodes: List of `lib.enm_node.Node` instances

    :raises ScriptEngineResponseValidationError: raised if no cells found on node

    :rtype: list
    :return: list of geran cell id
    """
    geran_cell_ids = []
    for node in nodes:
        response = execute_command_on_enm_cli(users[0], GET_GERANCELL_ON_NODE.format(node_id=node.node_id))
        output = response.get_output()
        for cell in [item for item in output if "GeranCell=".lower() in item.lower()]:
            geran_cell_ids.append(cell.split("GeranCell=")[1].strip())
        if any(re.search(r'(error)', line, re.I) for line in response.get_output()) or not geran_cell_ids:
            raise ScriptEngineResponseValidationError("ScriptEngineResponse contains"
                                                      " zero geran cells in node {0}"
                                                      " Response was {1}".format(node.node_id,
                                                                                 ','.join(output)), response=response)

    return geran_cell_ids
