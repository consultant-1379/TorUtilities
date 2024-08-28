# ********************************************************************
# Name    : Reparenting
# Summary : Functional module for use by the reparenting flows to
#           interact with the reparenting rest endpoints, and generate
#           the required JSON payload(s) for the respective endpoints.
# ********************************************************************
import re
import time
from requests import HTTPError

from enmutils.lib import log
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib.headers import JSON_SECURITY_REQUEST

BASE_URL = "/reparent/v1/"
CANDIDATE_CELLS_URl = "determine-candidate-cells"
IMPACT_URL = "determine-impacts"
DELETE_CANDIDATE_CELLS_URL = "determine-delete-candidate-cells"
CONFLICTING_RELATIONS_URL = "determine-reparented-conflicting-relations"
CONFLICTING_DELETE_RELATIONS_URL = "determine-delete-conflicting-relations"
REPARENTED_CELLS_URL = "determine-reparented-cells"
REPARENTED_RELATIONS_BASE_URL = "determine-reparented-relations"
RELATION_TYPES_INTRA_RAT_URL = "{0}?relationTypes=INTRA_RAT".format(REPARENTED_RELATIONS_BASE_URL)
RELATION_TYPES_INTER_RAT_URL = "{0}?relationTypes=INTER_RAT".format(REPARENTED_RELATIONS_BASE_URL)
CUTOVER_CANDIDATE_CELLS_URL = "determine-cutover-candidate-cells"
CUTOVER_REPARENTED_CELLS_URL = "determine-cutover-reparented-cells"
CUSTOMIZE_REPARENTED_CELLS_URL = "determine-customize-reparented-cells"
DELETE_CANDIDATE_RELATIONS_URL = "determine-delete-candidate-relations"
REQUEST_URL = "{0}request/".format(BASE_URL)
MO_G12TG = "G12Tg.connectedChannelGroup"
MO_G31TG = "G31Tg.connectedChannelGroup"
MO_GERANCELL = "GeranCell"
MO_CONNECTED_MSC = "connectedMsc"
ATTRIBUTE = "connectedChannelGroup"
INTER_RAN = "InterRanMobility prioCr"
FDN_KEY = "FDN"
BASE_MSG = "Getting {0} information for the supplied BSC ids."
COMPLETED_MSG = "Completed getting {0} information for the supplied BSC ids."


def send_post_request(user, url, json):
    """
    Makes a POST request to reparenting application

    :param user: User who make the POST request to ENM
    :type user: `enm_user_2.User`
    :param url: The reparenting URL to be used for the POST request
    :type url: str
    :param json: The JSON payload to be sent in the POST request
    :type json: dict

    :return: Response object returned by the GET request
    :rtype: `request.Response`
    """
    response = user.post("{0}{1}".format(BASE_URL, url), json=json, headers=JSON_SECURITY_REQUEST)
    raise_for_status(response)
    log.logger.debug("\nURL::\t{0}\nJSON::\t{1}\n".format(url, json))
    return response


def get_status_request(user, resource_id):
    """
    Makes a GET request to reparenting application using the supplied resource Id

    :param user: User who make the GET request to ENM
    :type user: `enm_user_2.User`
    :param resource_id: The ID returned in the response of the initial POST request
    :type resource_id: str

    :return: Response object returned by the GET request
    :rtype: `request.Response`
    """
    response = user.get("{0}{1}".format(REQUEST_URL, resource_id))
    raise_for_status(response)
    return response


def build_base_station_json(base_stations, technology_type=None, target_network_controller=None):
    """
    Function to build the JSON to be used by the base station requests

    :param base_stations: List of base station FDNs to be supplied to the service
    :type base_stations: list
    :param technology_type: The technology domain of the base stations, for example GSM
    :type technology_type: str
    :param target_network_controller: The NetworkElement the base stations are to be moved to
    :type target_network_controller: str

    :return: The dictionary to be sent to the REST endpoint
    :rtype: dict
    """
    target_base_stations = [{'fdn': base_station} for base_station in base_stations]
    base_json = {"baseStations": target_base_stations}
    if technology_type:
        base_json.update({"technologyType": technology_type})
    if target_network_controller:
        base_json.update({"targetNetworkController": "NetworkElement={0}".format(target_network_controller)})
    return base_json


def build_cell_json(base_stations, technology_type=None, target_network_controller=None, include_mo_operations=None,
                    include_attributes=None, target_cells=None):
    """
    Function to build the JSON to be used by the cell requests

    :param technology_type: The technology domain of the cells, for example GSM
    :type technology_type: str
    :param target_network_controller: The NetworkElement the cells are to be moved to
    :type target_network_controller: str
    :param include_mo_operations: Boolean indicating the related MSC should be updated
    :type include_mo_operations: bool
    :param base_stations: List of base station FDNs with their cells to be supplied to the service
    :type base_stations: list
    :param include_attributes: Boolean indicating if additional attribute are needed for each cell
    :type include_attributes: bool
    :param target_cells: List of the cells on the target BSC
    :type target_cells: list

    :return: The dictionary to be sent to the REST endpoint
    :rtype: dict
    """
    base_json = {}
    stations = []
    count = 100
    index = 0
    for base_station_with_cells in base_stations:
        for base_station, cells in base_station_with_cells.items():
            candidate_cells = [{"candidateFdn": cell} for cell in cells]
            if include_attributes and target_cells:
                for candidate_cell in candidate_cells[:]:
                    candidate_cell.update({'newName': target_cells[index].split('=')[-1], 'newLac': count})
                    index += 1
                    count += 1
            stations.append({'fdn': base_station, 'cells': candidate_cells})
    base_json.update({"baseStations": stations})
    if technology_type:
        base_json.update({"technologyType": technology_type})
    if target_network_controller:
        base_json.update({"targetNetworkController": "NetworkElement={0}".format(target_network_controller)})
    if include_mo_operations is not None:
        base_json.update({"includeMscOperations": include_mo_operations})
    return base_json


def get_bsc_network_elements(user):
    """
    Function to query ENM for the available BSC id(s).

    :param user: User who execute the ENM command
    :type user: `enm_user_2.User`

    :return: List containing the available BSC node id(s)
    :rtype: list
    """
    network_elements = []
    log.logger.debug("Query ENM for available BSC NetworkElement id(s).")
    cmd = "cmedit get * NetworkElement -ne=BSC"
    response = user.enm_execute(cmd)
    if validate_response(response):
        network_elements = [line.split('NetworkElement=')[-1].strip() for line in response.get_output() if
                            FDN_KEY in line]
    log.logger.debug("Completed querying ENM for available BSC NetworkElement id(s).")
    return network_elements


def get_tg_mos(user, node_ids, geran_cells):
    """
    Function to get the G12Tg/G31Tg MO(s) of the supplied BSC node id(s)

    :param user: User who execute the ENM command
    :type user: `enm_user_2.User`
    :param node_ids: List of node IDs to query in ENM
    :type node_ids: list
    :param geran_cells: Dictionary containing Geran cells sorted by BSC
    :type geran_cells: dict

    :return: Dictionary containing the G12Tg/G31Tg MO(s) of the supplied BSC node id(s)
    :rtype: dict
    """
    tgs_channel_groups = {}
    mo_str = "{0}/{1}".format(MO_G12TG, MO_G31TG)
    log.logger.debug(BASE_MSG.format(mo_str))
    for node_id in node_ids:
        for mo in [MO_G31TG, MO_G12TG]:
            cmd = "cmedit get {0} {1}".format(node_id, mo)
            response = user.enm_execute(cmd)
            if validate_response(response):
                output = response.get_output()
                for index, line in enumerate(output):
                    if FDN_KEY in line:
                        tgmo = line.split(':')[-1].strip()
                        channel_group_value = output[index + 1].split(':')[-1].strip().replace('[', '').replace(
                            ']', '').split(' ')
                        tgs_channel_groups[tgmo] = remove_missing_cells(channel_group_value, geran_cells)
    log.logger.debug(COMPLETED_MSG.format(mo_str))
    return tgs_channel_groups


def get_and_sort_geran_cells(user):
    """
    Function to get the Geran Cells on the deployment

    :param user: User who execute the ENM command
    :type user: `enm_user_2.User`

    :returns: Dictionary containing Geran cells sorted by BSC
    :rtype: dict
    """
    cmd = "cmedit get * GeranCell"
    response = user.enm_execute(cmd)
    sorted_cells = {}
    if validate_response(response):
        output = response.get_output()
        for line in output:
            if FDN_KEY in line:
                bsc = line.split('ManagedElement=')[-1].split(',')[0]
                if bsc not in sorted_cells.keys():
                    sorted_cells[bsc] = []
                sorted_cells[bsc].append(line.split(":")[-1].strip())
    return sorted_cells


def remove_missing_cells(connected_channel_groups, geran_cells):
    """
    Function to filter out connected channel groups which no longer exist

    :param connected_channel_groups: The list of connected channel groups to be verified
    :type connected_channel_groups: list
    :param geran_cells: Dictionary containing Geran cells sorted by BSC
    :type geran_cells: dict

    :return: List of updated connected channel groups
    :rtype: list
    """
    log.logger.debug("Verifying cells exist.")
    for connected_channel_group in connected_channel_groups[:]:
        bsc = connected_channel_group.split('ManagedElement=')[-1].split(',')[0]
        if (bsc in geran_cells.keys() and connected_channel_group.split(',ChannelGroup')[0] not
                in geran_cells.get(bsc)):
            connected_channel_groups.remove(connected_channel_group)
    log.logger.debug("Completed verifying cells exist.")
    return connected_channel_groups


def set_channel_group_active(user, channel_groups):
    """
    Function to set the selected channel groups to acive state

    :param user: User who make the GET request to ENM
    :type user: `enm_user_2.User
    :param channel_groups: selected cells
    :type channel_groups: list
    """
    log.logger.debug("Setting channelGroup to active state.")
    cmd = "cmedit set {0} state=ACTIVE --force"
    try:
        for channel_group in channel_groups:
            user.enm_execute(cmd.format(channel_group))
            log.logger.debug("Successfully set the channelGroup to active state.")
    except Exception as e:
        log.logger.debug("The issue occured while setting channelGroup to active state due to {0}.".format(e))


def set_inter_ran_mobility_attribute(user, geran_cells, enum_value):
    """
    Function to set the INTER RAN Mobility MO attribute

    :param user: User who execute the ENM command
    :type user: `enm_user_2.User`
    :param geran_cells: List containing Geran cells
    :type geran_cells: list
    :param enum_value: The ENUM value to be set ON|OFF
    :type enum_value: str
    """
    log.logger.debug("Attempting to set {0} {1} cells to:: [{2}].".format(INTER_RAN, len(geran_cells),
                                                                          enum_value.upper()))
    cmd = "cmedit set {0} {1}:{2} --force".format(";".join([cell for cell in geran_cells]), INTER_RAN,
                                                  enum_value.upper())
    response = user.enm_execute(cmd)
    log.logger.debug("Set {0} for {1} cells to:: [{2}] result:: {3}.".format(
        INTER_RAN, len(geran_cells), enum_value.upper(), validate_response(response)))


def validate_response(response):
    """
    Validate the supplied ENM response has output and contains instance value(s)

    :param response: Response object to be validated
    :type response: `request.Response`
    :return: Boolean indicating if the response contains valid instances
    :rtype: bool
    """
    valid = False
    log.logger.debug("Validating response of enm execute command: {0}".format(getattr(response, 'command', '')))
    if (response and response.get_output() and
            not any(re.search(r'(error|^[0]\sinstance)', line, re.I) for line in response.get_output())):
        valid = True
    log.logger.debug("Completed validating response of enm execute command, valid: {0}".format(valid))
    return valid


def poll_for_completed_status(user, resource_id, timeout):
    """
    Function to poll the service for the completion of the POST request

    :param user: User who make the GET request to ENM
    :type user: `enm_user_2.User`
    :param resource_id: The ID returned in the response of the initial POST request
    :type resource_id: str
    :param timeout: Timeout to wait before
    :type timeout: int

    :raises EnmApplicationError: raised if the polling times out or the get request fails

    :return: Boolean indicating if the request was successful
    :rtype: bool
    """
    start_time = time.time()
    sleep_interval = 30
    log.logger.debug("Sleeping for {0} seconds before attempting to retrieve status.".format(sleep_interval))
    time.sleep(sleep_interval)
    while time.time() <= start_time + timeout:
        try:
            response = get_status_request(user, resource_id)
        except HTTPError as e:
            if e.response.status_code == 500:
                break
            log.logger.debug(
                "Unable to get status of resource: [{0}], retrying in {1} seconds. Error encountered: {2}".format(
                    resource_id, sleep_interval, str(e)))
            time.sleep(sleep_interval)
            continue
        else:
            if check_status_code(response):
                return True
            else:
                log.logger.debug(
                    "Status of response is currently: {0}, sleeping for {1} seconds before retrying.".format(
                        response.status_code, sleep_interval))
                time.sleep(sleep_interval)
    raise EnmApplicationError("Failed to retrieve status of resource ID:: [{0}], please check the logs for more "
                              "information.".format(resource_id))


def check_status_code(response):
    """
    Function to validate the HTTP Response returned by the GET request

    :param response: HTTP Response object
    :type response: `response.HTTPResponse`

    :raises EnmApplicationError: raised if no content returned

    :return: Boolean if the status code is successful
    :rtype: bool
    """
    status_code = response.status_code
    if status_code in [200]:
        output = response.json()
        if ('cells' in output.keys() and not output.get('cells') or
                'operations' in output.keys() and not output.get('operations')):
            raise EnmApplicationError("Response validation failed:\nResponse::\n{0}\n".format(output))
        output_str = str(output)
        output = "{0}.........{1}".format(output_str[:400], output_str[-400:]) if len(
            output_str) > 800 else output
        log.logger.debug("Status polling completed, status code: {0}\nResponse::\n{1}\n".format(status_code, output))
        return True
