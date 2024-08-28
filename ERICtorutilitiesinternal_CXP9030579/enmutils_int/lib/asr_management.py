# ****************************************************************************************
# Name    : Analytic Session Record (ASR)
# Summary : Module for perform the Analytic session record management operations.
#            1. Get ASRL/ASRN configuration status from ENM.
#            2. Update ASR Record.
#            3. Get all ASR records info.
#            4. Get ASR record info based on record id (poid).
#            5. Get ASR record info based on record type.
#            6. Activate and Deactivate the ASR record.
#            7. Perform ASR(ASR_L/ASR_N) pre conditions.
#            8. Perform ASR(ASR_L,ASR_N) post conditions.
#            9. Wait for ASR record to active state.
#            10. Check if ASR Record (ASR_L, ASR_N) NB IP Port configured in ENM
#            11. Check if ASR Record (ASR_L, ASR_N) NB IP Port configured in network file.
# ****************************************************************************************

import datetime
import json
import time
from functools import partial

from enmutils.lib.headers import JSON_SECURITY_REQUEST
from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError, EnvironError, TimeOutError

ASR_CONFIG_STATUS_CMD = "cmedit get {asr_configuration_type}={asr_type}"
ALL_ASR_RECORDS = "/session-record/v1/record-configs"
ASR_RECORD = ALL_ASR_RECORDS + "/{record_id}"
ASR_RECORD_TYPES = ["ASR_L", "ASR_N"]
SUPPORTED_ASR_RECORD_STATES = ['ACTIVATING', 'DEACTIVATING']
SLEEP_FOR_ASR_RECORD_ACTIVE_STATUS = 7


def get_asr_config_status(user, asr_record_type):
    """
    Get ASRL/ASRN config status based on asr record type from enm.

    :type user: enm_user_2.User
    :param user: User instance
    :type asr_record_type: str
    :param asr_record_type: asr record type. ASR-L, ASR-N

    :return: True if ASRL/ASRN configured in ENM, otherwise False
    :rtype: bool
    """
    log.logger.debug("Checking {0} configuration status".format(asr_record_type))
    asr_config_status = False
    response = user.enm_execute(ASR_CONFIG_STATUS_CMD.format(
        asr_configuration_type=("ASRLConfiguration" if asr_record_type == "ASR-L" else "ASRNConfiguration"),
        asr_type=asr_record_type))
    if '0 instance(s)' not in response.get_output():
        asr_config_status = True
    log.logger.debug("Status of {0} configuration : {1}".format(asr_record_type, asr_config_status))
    return asr_config_status


def update_asr_record(user, asr_record_info):
    """
    Update ASR Record in ENM

    :type user: enm_user_2.User
    :param user: User instance
    :type asr_record_info: dict
    :param asr_record_info: dictionary of asr record info

    :return: returns status of ASR record
    :rtype: dict

    :raises EnmApplicationError: if getting empty response
    """
    asr_record_id = asr_record_info["poid"]
    asr_record_type = asr_record_info["type"]
    log.logger.debug("Attempting to update the {0} record and payload: {1}".format(asr_record_type,
                                                                                   asr_record_info))
    response = user.put(ASR_RECORD.format(record_id=asr_record_id), data=json.dumps(asr_record_info),
                        headers=JSON_SECURITY_REQUEST)
    response.raise_for_status()
    json_response = response.json()
    log.logger.debug("Response of {0} record: {1}".format(asr_record_type, json_response))
    if not json_response:
        raise EnmApplicationError("Failed to update the {0} record".format(asr_record_type))
    log.logger.debug("Successfully updated {0} record: {1}".format(asr_record_type, json_response))

    return json_response


def get_all_asr_records_info(user):
    """
    Get all ASR Records info from ENM.

    :type user: enm_user_2.User
    :param user: User instance

    :return: returns asr records details
    :rtype: list
    """
    log.logger.debug("Attempting to get all ASR records info")
    response = user.get(ALL_ASR_RECORDS, headers=JSON_SECURITY_REQUEST)
    response.raise_for_status()
    json_response = response.json()
    log.logger.debug("Successfully fetched all ASR records info")

    return json_response


def get_asr_record_info_based_on_id(user, record_id):
    """
    Get ASR Record info from ENM based on record id (poid).

    :type user: enm_user_2.User
    :param user: User instance
    :type record_id: str
    :param record_id: poid of asr record

    :return: returns asr record details
    :rtype: dict
    """
    log.logger.debug("Attempting to get ASR record info for {0}".format(record_id))
    response = user.get(ASR_RECORD.format(record_id=record_id), headers=JSON_SECURITY_REQUEST)
    response.raise_for_status()
    json_response = response.json()
    log.logger.debug("Successfully fetched ASR record info for {0}".format(record_id))

    return json_response


def get_asr_record_info_based_on_type(user, asr_record_type):
    """
    Get ASRL Record info from ENM based on record type

    :type user: enm_user_2.User
    :param user: User instance
    :type asr_record_type: str
    :param asr_record_type: asr record type. ASR_L, ASR_N

    :return: returns asr record details
    :rtype: list
    :raises EnvironError: if ASR records not found in ENM
    """
    log.logger.debug("Attempting to get {0} record info".format(asr_record_type))
    asr_records_info = get_all_asr_records_info(user)
    if asr_records_info:
        asr_record_info = [record for record in asr_records_info if record['type'] == asr_record_type]
        log.logger.debug("Successfully fetched {0} record info : {1}".format(asr_record_type, asr_record_info))
    else:
        raise EnvironError("ASR records not found in ENM")

    return asr_record_info


def activate_and_deactivate_asr_record(user, asr_record_info, action):
    """
    Activate or Deactivate the ASR record

    :type user: enm_user_2.User
    :param user: User instance
    :type asr_record_info: dict
    :param asr_record_info: asr record info
    :type action: str
    :param action: ACTIVATING, DEACTIVATING

    :return: returns status of ACTIVATING/DEACTIVATING ASR record
    :rtype: dict

    :raises HttpError: if response status is not ok
    :raises EnmApplicationError: if getting empty response
    """
    action_status = "Activate" if action == "ACTIVATING" else "Deactivate"
    asr_record_type = asr_record_info["type"]
    log.logger.debug("Attempting to {0} the {1} record".format(action_status, asr_record_type))
    asr_record_info["administrationState"] = action
    log.logger.debug("{0} the {1} record payload: {2}".format(action_status, asr_record_type, asr_record_info))
    response = user.put(ASR_RECORD.format(record_id=asr_record_info["poid"]), data=json.dumps(asr_record_info),
                        headers=JSON_SECURITY_REQUEST)
    response.raise_for_status()
    json_response = response.json()
    log.logger.debug("Response to the {0} action for {1} record: {2}".format(action_status, asr_record_type,
                                                                             json_response))
    if not json_response:
        raise EnmApplicationError("The {0} action failed for {1} record".format(action_status, asr_record_type))
    log.logger.debug("Successfully initialized the {0} record {1} process: {2}".format(asr_record_type, action_status,
                                                                                       json_response))
    return json_response


def perform_asr_preconditions_and_postconditions(profile, profile_nodes, asr_record_type):
    """
    Gets PM synced nodes based on number of cells with required mo type and Performs ASRN preconditions and
    postconditions.

    :type profile: 'enmutils_int.lib.profile.Profile`
    :param profile: Profile object
    :type profile_nodes: list
    :param profile_nodes: nodes
    :type asr_record_type: str
    :param asr_record_type: asr record type. ASR-L, ASR-N

    """
    try:
        nodes_poids = [node.poid for node in profile_nodes]
        asr_record_update_status = perform_asr_preconditions(profile, nodes_poids, asr_record_type)
        perform_asr_postconditions(profile, asr_record_update_status, asr_record_type)
    except Exception as e:
        profile.add_error_as_exception(e)


def perform_asr_preconditions(profile, nodes_poids, asr_record_type):
    """
    This method performs some set of operations such as get asr record info based on type, update asr record

    :type profile: `enmutils_int.lib.profile.Profile`
    :param profile: Profile object
    :type nodes_poids: list
    :param nodes_poids: poid's of nodes.
    :type asr_record_type: str
    :param asr_record_type: asr record type. ASR-L, ASR-N

    :return: returns update status of ASR record
    :rtype: dict

    :raises EnvironError: if getting empty response
    """
    log.logger.debug("Performing the ASR pre conditions")
    asr_record = get_asr_record_info_based_on_type(profile.USER, asr_record_type)
    if asr_record:
        log.logger.debug("Updating the nodes poid's for add the nodes in {0} record".format(asr_record_type))
        asr_record[0].update({"resourcesPoIds": nodes_poids,
                              "streamInfo": {"ipAddress": profile.NB_IP, "port": profile.PORT}})
        asr_record_update_status = update_asr_record(profile.USER, asr_record[0])
        log.logger.debug("Sleeping for {0} sec before activating the {1} record".format(profile.SLEEP_TIME,
                                                                                        asr_record_type))
        time.sleep(profile.SLEEP_TIME)
        if not asr_record_update_status:
            raise EnvironError("Failed to get the {0} record".format(asr_record_type))
        return asr_record_update_status
    else:
        raise EnvironError("{0} record is not existed in ENM".format(asr_record_type))


def perform_asr_postconditions(profile, asr_record_update_status, asr_record_type):
    """
    This method performs some set of operations such as activate the asr record,
    wait for asr record to active state

    :type profile: `enmutils_int.lib.profile.Profile`
    :param profile: Profile object
    :type asr_record_update_status: dict
    :param asr_record_update_status: asr record info
    :type asr_record_type: str
    :param asr_record_type: asr record type. ASR-L, ASR-N
    :raises EnvironError: Failed to get the ASR(ASR_L/ASR_N) record activate status
    """
    log.logger.debug("Performing the {0} post conditions".format(asr_record_type))
    asr_record_active_status = activate_and_deactivate_asr_record(profile.USER, asr_record_update_status,
                                                                  SUPPORTED_ASR_RECORD_STATES[0])
    if asr_record_active_status:
        asr_record_status = wait_asr_record_to_active_state(profile.USER, asr_record_active_status["poid"],
                                                            profile.SLEEP_TIME)
        profile.teardown_list.append(partial(wait_asr_record_to_deactivate_state, profile.USER,
                                             asr_record_active_status["poid"], profile.SLEEP_TIME))
        profile.teardown_list.append(partial(activate_and_deactivate_asr_record, profile.USER, asr_record_status,
                                             SUPPORTED_ASR_RECORD_STATES[1]))
    else:
        raise EnvironError("Failed to get the {0} record activate status".format(asr_record_type))


def wait_asr_record_to_active_state(user, record_id, sleep_time):
    """
    wait and checks for ASR record administrationState to become 'ACTIVE'

    :type user: enm_user_2.User
    :param user: User instance
    :type record_id: str
    :param record_id: poid of asr record
    :type sleep_time: int
    :param sleep_time: sleep time for asr record activation
    :rtype: dict
    :return: asr record activation status

    :raises TimeOutError: when ASR record state cannot be verified within given time
    """
    log.logger.debug("Checking the activation status of ASR Record")
    expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=SLEEP_FOR_ASR_RECORD_ACTIVE_STATUS)
    while datetime.datetime.now() < expiry_time:
        asr_record = get_asr_record_info_based_on_id(user, record_id)
        if asr_record and asr_record["administrationState"] == "ACTIVE":
            log.logger.debug("Successfully Activated {0} record".format(asr_record["type"]))
            return asr_record
        log.logger.debug("ASR record is still in activating state, "
                         "Sleeping for {0} seconds before re-trying..".format(sleep_time))
        time.sleep(sleep_time)

    raise TimeOutError("Cannot verify the activation state of ASR record")


def wait_asr_record_to_deactivate_state(user, record_id, sleep_time):
    """
    wait and checks for ASR record administrationState to become 'INACTIVE'

    :type user: enm_user_2.User
    :param user: User instance
    :type record_id: str
    :param record_id: poid of asr record
    :type sleep_time: int
    :param sleep_time: sleep time for asr record activation
    :rtype: dict
    :return: asr record deactivation status

    :raises TimeOutError: when ASR record state cannot be verified within given time
    """
    log.logger.debug("Checking the deactivation status of ASR Record")
    expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=SLEEP_FOR_ASR_RECORD_ACTIVE_STATUS)
    while datetime.datetime.now() < expiry_time:
        asr_record = get_asr_record_info_based_on_id(user, record_id)
        if asr_record and asr_record["administrationState"] == "INACTIVE":
            log.logger.debug("Successfully Deactivated {0} record".format(asr_record["type"]))
            return asr_record
        log.logger.debug("ASR record is still in deactivating state, "
                         "Sleeping for {0} seconds before re-trying..".format(sleep_time))
        time.sleep(sleep_time)

    raise TimeOutError("Cannot verify the deactivation state of ASR record")


def check_if_asr_record_nb_ip_port_configured(profile, asr_record_type):
    """
    Check whether NB IP, Port configured or not for ASR(ASR_L/ASR_N) Record .

    :return: NB IP, Port configured status for ASR(ASR_L/ASR_N) record in network file. True, False
    :rtype: bool
    """
    log.logger.debug("Checking NB IP, Port configuration status for {0} record".format(asr_record_type))
    nbip_port_config_status_of_asr_record = False
    if (check_if_asr_record_nb_ip_port_configured_in_enm(profile, asr_record_type) or
            check_if_asr_record_nb_ip_port_configured_in_network_file(profile.USER, asr_record_type)):
        nbip_port_config_status_of_asr_record = True
    log.logger.debug("Status of NB IP, Port configuration for {0} in ENM: {1}".format(
        asr_record_type, nbip_port_config_status_of_asr_record))
    return nbip_port_config_status_of_asr_record


def check_if_asr_record_nb_ip_port_configured_in_enm(profile, asr_record_type):
    """
    Check whether NB IP, Port configured or not for ASR_L/ASR_N Record in ENM.

    :type profile: `enmutils_int.lib.profile.Profile`
    :param profile: Profile object
    :type asr_record_type: str
    :param asr_record_type: asr record type. ASR_L, ASR_N

    :return: NB IP, Port configured status for ASR record in enm. True, False
    :rtype: bool

    """
    log.logger.debug("Checking NB IP, Port configuration status for {0} in ENM".format(asr_record_type))
    nbip_port_config_status_of_asr_record = False
    asr_record = get_asr_record_info_based_on_type(profile.USER, asr_record_type)
    if asr_record:
        if ("streamInfo" in asr_record[0] and "ipAddress" in asr_record[0]["streamInfo"] and
                asr_record[0]["streamInfo"]["ipAddress"] and "port" in asr_record[0]["streamInfo"] and
                asr_record[0]["streamInfo"]["port"]):
            nbip_port_config_status_of_asr_record = True
            profile.NB_IP = asr_record[0]["streamInfo"]["ipAddress"]
            profile.PORT = asr_record[0]["streamInfo"]["port"]
    else:
        log.logger.debug("{0} record is not existed in ENM".format(asr_record_type))
    log.logger.debug("Status of NB IP, Port configuration for {0} in ENM: {1}".format(
        asr_record_type, nbip_port_config_status_of_asr_record))
    return nbip_port_config_status_of_asr_record


def check_if_asr_record_nb_ip_port_configured_in_network_file(profile, asr_record_type):
    """
    Check whether NB IP, Port configured or not for ASR_L/ASR_N Record in network file.

    :type profile: `enmutils_int.lib.profile.Profile`
    :param profile: Profile object
    :type asr_record_type: str
    :param asr_record_type: asr record type. ASR_L, ASR_N

    :return: NB IP, Port configured status for ASR record in network file. True, False
    :rtype: bool
    """
    log.logger.debug("Checking NB IP, Port configuration status for {0} record in network file".format(asr_record_type))
    nbip_port_config_status_of_asr_record = False
    if profile.NB_IP and profile.PORT:
        nbip_port_config_status_of_asr_record = True
    log.logger.debug("Status of NB IP, Port configuration for {0} record in network file: {1}".format(
        asr_record_type, nbip_port_config_status_of_asr_record))
    return nbip_port_config_status_of_asr_record
