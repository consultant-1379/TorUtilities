# ***************************************************************************************************************
# Name    : Flexible Counter Management (FCM)
# Summary : Module for perform the flexible Counter Management operations.
#           various functions related to flex counters management.
# ***************************************************************************************************************

import json
import time

from enmutils.lib.headers import JSON_SECURITY_REQUEST
from enmutils.lib import log, filesystem
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils_int.lib.common_utils import get_internal_file_path_for_import


FLEX_COUNTERS = "/ebscountermanagement/flex/counters"
IMPORT_FLEX_COUNTERS = "ebscountermanagement/flex/importGeoR"
FLEX_COUNTERS_1000_FILE_PATH = get_internal_file_path_for_import("etc", "data", "flex_counters_1000.json")
FLEX_COUNTERS_50_FILE_PATH = get_internal_file_path_for_import("etc", "data", "flex_counters_50.json")


def get_flex_counters(user):
    """
    Get list of flex counters from ENM FCM.

    :param user: User instance
    :type user: enm_user_2.User
    :return: returns list of flex counters.
    :rtype: list

    :raises HttpError: if response status is not ok
    """
    log.logger.debug("Attempting to get flex counters from ENM")
    response = user.get(FLEX_COUNTERS, headers=JSON_SECURITY_REQUEST)
    response.raise_for_status()
    json_response = response.json()

    flex_counters_names = ",".join([flex_counter["flexCounterName"] for flex_counter in json_response])
    log.logger.debug("Successfully fetched flex counters: {0} from ENM: {1}".format(len(json_response),
                                                                                    flex_counters_names))
    return json_response


def import_flex_counters_in_enm(user, file_path):
    """
    Import flex counters using flex counters json file in enm. flex counters will be create in enm.

    :param user: User instance
    :type user: enm_user_2.User
    :param file_path: flex counters json file path
    :type file_path: str

    :return: returns dict, it contains JobId,total Flex Counters, Total Failed Flex Counters.
    :rtype: dict

    :raises HttpError: if response status is not ok
    :raises EnmApplicationError: if getting empty response
    """
    log.logger.debug("Attempting to import flex counters using {0} in ENM".format(file_path))
    with open(file_path, "rb") as f:
        data = f.read()
    response = user.post(IMPORT_FLEX_COUNTERS, data=data, headers=JSON_SECURITY_REQUEST)
    response.raise_for_status()
    json_response = response.json()
    log.logger.debug("Response of import flex counters: {0}".format(json_response))
    if not json_response:
        raise EnmApplicationError("Failed to import flex counters in ENM: {0}".format(json_response))
    log.logger.debug("Successfully imported flex counters file into ENM")
    return json_response


def delete_flex_counters(user, flex_counters_names_list):
    """
    Delete flex counters in ENM, passing an array for multiple delete.

    :param user: User instance
    :type user: enm_user_2.User
    :param flex_counters_names_list: list of flex counters names
    :type flex_counters_names_list: list

    :return: returns dict, it contains JobId,total Flex Counters.
    :rtype: dict
    :raises HttpError: if response status is not ok
    """
    log.logger.debug("Attempting to delete flex counters")
    log.logger.debug("delete flex counters payload: {0}".format(flex_counters_names_list))
    response = user.delete_request(FLEX_COUNTERS, data=json.dumps(flex_counters_names_list),
                                   headers=JSON_SECURITY_REQUEST)
    response.raise_for_status()
    json_response = response.json()
    log.logger.debug("Successfully initialized delete flex counters: {0}".format(json_response))
    return json_response


def get_ebs_flex_counters(user):
    """
    get the EBS flex counters from ENM and build the counters json to add the counters to EBSN_04 subscription.

    :param user: User instance
    :type user: enm_user_2.User
    :return: returns list of flex counters
    :rtype: list
    :raises EnvironError: if Ebs flex counters are not existed in ENM.
    """
    ebs_counters = get_flex_counters(user)
    if ebs_counters:
        counters = []
        for counter in ebs_counters:
            if len(counter["sourceObject"]) > 1:
                for mo_class_type in counter["sourceObject"]:
                    counters.append({"name": counter["flexCounterName"], "moClassType": mo_class_type})
            else:
                counters.append({"name": counter["flexCounterName"], "moClassType": counter["sourceObject"][0]})
        return counters
    else:
        raise EnvironError("EBS Flex counters are not available in the ENM deployment")


def verify_creation_or_deletion_flex_counters_status(user, sleep_time, action, num_flex_counters_to_create):
    """
    Verifies the flex counters creation or deletion status.
    :param user: User instance
    :type user: enm_user_2.User
    :param sleep_time: number of seconds wait until create/delete flex counters process completed in ENM
    :type sleep_time: int
    :param action: action value create, delete
    :type action: str
    :param num_flex_counters_to_create: number of flex counters to create in ENM.
    :type num_flex_counters_to_create: int
    :raises EnvironError: if Ebs flex counters are not created in ENM.
    """
    log.logger.debug("Sleeping for {0} sec until {1} flex counters process completed in ENM".format(sleep_time, action))
    time.sleep(sleep_time)
    ebs_counters = get_flex_counters(user)
    if action == "create":
        if ebs_counters:
            log.logger.debug("{0} EBS Flex counters {1}d successfully out of {2} counters in ENM".format(
                len(ebs_counters), action, num_flex_counters_to_create))
        else:
            raise EnvironError("Flex counters are not {0}d in ENM deployment".format(action))
    else:
        log.logger.debug("{0} EBS Flex counters {1}d successfully out of {2} counters in ENM".format(
            num_flex_counters_to_create - len(ebs_counters), action, num_flex_counters_to_create))


def get_reserved_ebsn_flex_counters(profile_name):
    """
    Get reserved ebsn flex counters names from json file
    :return: returns list of flex counters names
    :rtype: list
    """
    # In future change below condition, currently only in EBSN_01 and EBSN_03 we are removing flex counters
    file_path = FLEX_COUNTERS_1000_FILE_PATH if "EBSN_FILE_01" in profile_name else FLEX_COUNTERS_50_FILE_PATH
    reserved_flexible_counters = filesystem.read_json_data_from_file(file_path, raise_error=False)
    reserved_flexible_counters = [counter["flexCounterName"] for counter in reserved_flexible_counters]
    log.logger.debug("Successfully fetched reserved flexible {0} counters "
                     "from {1}".format(len(reserved_flexible_counters), file_path))
    return reserved_flexible_counters


def remove_any_existing_flexible_counters(user, sleep_time):
    """
    Check and delete old EBS flexible counters in ENM
    :param user: User instance
    :type user: enm_user_2.User
    :param sleep_time: number of seconds wait until delete flex counters process completed in ENM
    :type sleep_time: int
    """
    log.logger.debug("Checking and deleting the old ebs flexible counters")
    ebs_counters = get_flex_counters(user)
    if ebs_counters:
        flex_counters_names = [counter['flexCounterName'] for counter in ebs_counters]
        log.logger.debug("{0} old ebs flexible counters are available in the ENM "
                         "deployment".format(len(flex_counters_names)))
        delete_flex_counters(user, flex_counters_names)
        verify_creation_or_deletion_flex_counters_status(user, sleep_time, "delete", len(flex_counters_names))
    else:
        log.logger.debug("Old EBS Flex counters do not exist in the ENM deployment")
