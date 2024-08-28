# ********************************************************************
# Name    : NHC (Network Health Check)
# Summary : Functional module used by NHC profiles. Allows user to
#           create Network Health Check job and convert datetime to a
#           compatible time supported by the NHC application.
# ********************************************************************

import json
from datetime import datetime
from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError
from enmutils.lib.headers import JSON_SECURITY_REQUEST
from retrying import retry
from requests.exceptions import HTTPError, ConnectionError

NHC_JOB_CREATE_URL = 'nhcservice/report/v1/newreport'
NHC_PROFILE_CREATE_URL = 'nhcprofileservice/profile/v1/newprofile'
NHC_PROFILE_DELETE_URL = 'nhcprofileservice/v1/profiles/delete'
NHC_PROFILE_RULES_URL = 'nhcprofileservice/profile/v1/rulesdefinition'
NHC_PROFILE_LIST_URL = 'nhcprofileservice/profile/v1/list'
NHC_JOB_LIST_URL = 'nhcservice/report/v1/list'
NHC_JOB_CANCEL_URL = 'nhcservice/report/v1/cancel/'
NHC_JOB_DELETE_URL = 'nhcservice/report/v1/delete/'
GET_TIME_OFFSET_URL = '/oss/shm/rest/servertime/getTimeOffset'
GET_RADIO_NODE_PACKAGE_URL = 'nhcprofileservice/profile/v1/softwarepackages/RadioNode'

NHC_JOB_LIST_PAYLOAD = {"offset": 1,
                        "limit": 5000,
                        "sortBy": "startTime",
                        "orderBy": "desc",
                        "filterDetails": []}

NHC_PROFILE_LIST_PAYLOAD = {"offset": 1,
                            "limit": 5000,
                            "sortBy": "creationTime",
                            "orderBy": "desc",
                            "filterDetails": []}

alarms_to_be_excluded = ("Cell Manually Locked;Server RDI*;HD Stack Configuration Fault;m3100AlarmIndicationSignal;"
                         "*Link Failure;*Loss of Signal;SS7 Stack Overloaded;Nss Synchronization System Clock Status Change;"
                         "SCB System Clock Path HW Fault;Automatic CV Creation Failed;Contact to Default Router 0 Lost;"
                         "NE and OSS alarms are not in sync;Duplicate IP Address Fault;EXTERNAL ALARM;"
                         "MTP3b Link Out of Service;Board Overheated;SS7 Cluster*;TU12 Loss of Pointer;"
                         "VC3 Remote Defect Indication;Switch Internal Link Port Fault")


def get_radio_node_package(user):
    """
    Returns the RadioNode package details imported from SHM
    :param user: enm user instance to be used to perform the get request
    :type user: `lib.enm_user.User`
    :return: Dict containing the package details
    :rtype: dict
    :raises EnmApplicationError: If it doesnt retrieve the package
    """
    log.logger.debug("Attempting to get RadioNode package for creating Health Check profile")
    response = user.get(GET_RADIO_NODE_PACKAGE_URL, headers=JSON_SECURITY_REQUEST)
    if response.status_code != 200:
        response.raise_for_status()
    if not response.json():
        raise EnmApplicationError("Failed to get the required RadioNode package for profile creation")
    package_dict = response.json()[0]
    log.logger.debug("Successfully retrieved the RadioNode package details for creating Health Check profile")
    return package_dict


def create_nhc_request_body(**kwargs):
    """
    This function constructs a payload for a NHC job creation

    :param kwargs: request values
    :type kwargs: dict

    :return: nhc_payload_body: payload
    :rtype: dict
    """

    name = kwargs.pop('name')
    time = kwargs.pop("time")
    ne_names = kwargs.pop('ne_elements')

    nhc_payload_body = {"name": name,
                        "description": "",
                        "jobType": "NODE_HEALTH_CHECK",
                        "configurations": [{"neType": "RadioNode",
                                            "properties": [{"key": "NODE_HEALTH_CHECK_TEMPLATE",
                                                            "value": "PREUPGRADE"}]}],
                        "mainSchedule": {"scheduleAttributes": [{"name": "START_DATE",
                                                                 "value": time}],
                                         "execMode": "SCHEDULED"},
                        "activitySchedules": [{"platformType": "ECIM",
                                               "value": [{"neType": "RadioNode",
                                                          "value": [{"activityName": "nodehealthcheck",
                                                                     "execMode": "IMMEDIATE",
                                                                     "order": 1,
                                                                     "scheduleAttributes": []}]}]}],
                        "neNames": ne_names,
                        "collectionNames": [],
                        "savedSearchIds": []}

    return nhc_payload_body


def get_profile_rules(user, ne_type, package_dict):
    """
    Returns the set of rules for the profile
    :param user: enm user instance to be used to perform the post request
    :type user: `lib.enm_user.User`
    :param ne_type: Node type of the network elements
    :type ne_type: str
    :param package_dict: Dict containing the package details
    :type package_dict: dict
    :return: Dict containing the rules to be used for the profile creation
    :rtype: dict
    :raises HTTPError: If it doesnt retrieve the profile rules
    """
    log.logger.debug("Attempting to get the rules required for profile creation")
    profile_rules_payload = {"neType": ne_type, "productNumber": package_dict['productNumber'],
                             "productRevision": package_dict['productRevision']}
    response = user.post(NHC_PROFILE_RULES_URL, data=json.dumps(profile_rules_payload),
                         headers=JSON_SECURITY_REQUEST)
    if response.ok:
        rules = [{"id": rule['id'], "name": rule["name"], "description": rule["description"],
                  "categories": rule["categories"], "technology": rule["technology"], "severity": rule["severity"],
                  "inputParameters": [{"value": parm["defaultValue"], "name": parm["name"]} for parm in
                                      rule["inputParameters"]]} for rule in response.json()["rules"]]
        updated_rules = update_profile_rules_to_ignore_alarm_checks(rules)
        log.logger.debug("Successfully retrieved the rules for the profile creation")
        return updated_rules
    else:
        raise HTTPError('Failed to get the rules required for the profile creation', response=response)


def update_profile_rules_to_ignore_alarm_checks(rules):
    """
    Returns the updated set of rules for the profile after excluding the user specified alarms
    :param rules: Dict containing the rules to be used for the profile creation
    :type rules: dict
    :return: Dict containing the updated rules to be used for the profile creation excluding specified alarms
    :rtype: dict
    """
    rules_to_update = ["CRITICAL-ALARM-CHECK", "MAJOR-ALARM-CHECK"]
    for rule in rules:
        if rule["id"] in rules_to_update:
            for input_parameter in rule["inputParameters"]:
                if input_parameter["name"] == 'ignoreSpecificProblems':
                    input_parameter["value"] = alarms_to_be_excluded
    return rules


def nhc_profile_payload(user, name, ne_type, package, rules):
    """
    Creates the payload for the profile creation
    :param user: enm user instance to be used to perform the post request
    :type user: `lib.enm_user.User`
    :param name: profile name
    :type name: str
    :param ne_type: Node type of the network elements
    :type ne_type: str
    :param package: Dict containing the package details
    :type package: dict
    :param rules: Dict containing the rules to be used for the profile creation
    :type rules: dict
    :return: payload
    :rtype: dict
    """
    log.logger.debug("Attempting to create payload for profile creation request")
    payload = {"name": name,
               "description": "",
               "neType": ne_type,
               "packageName": package['packageName'],
               "productNumber": package['productNumber'],
               "productRevision": package['productRevision'],
               "productRelease": package['productRelease'],
               "createdBy": user.username,
               "profileRules": rules,
               "userLabel": []}
    log.logger.debug("Payload for creating profile successfully created")
    return payload


def create_nhc_profile(user, ne_type, package_dict, name):
    """
    Creates the profile required for the Node Health Check Job
    :param user: enm user instance to be used to perform the post request
    :type user: `lib.enm_user.User`
    :param ne_type: Node type of the network elements
    :type ne_type: str
    :param package_dict: Dict containing the package details
    :type package_dict: dict
    :param name: Name of the profile
    :type name: str
    :return: Returns the name of the profile created
    :rtype: str
    :raises HTTPError: If the profile creation response is not ok
    """
    profile_rules = get_profile_rules(user, ne_type, package_dict)
    profile_name = name + "_HealthCheckProfile_administrator_" + datetime.now().strftime(
        "%Y%m%d%H%M%S")
    profile_payload = nhc_profile_payload(user=user, name=profile_name, ne_type=ne_type,
                                          package=package_dict, rules=profile_rules)
    log.logger.debug("Attempting to create profile-{0}".format(profile_name))
    response = user.post(NHC_PROFILE_CREATE_URL, data=json.dumps(profile_payload),
                         headers=JSON_SECURITY_REQUEST)
    if response.ok and response.json():
        created_profile_name = response.json().get('name')
        log.logger.debug("Profile:{0} has been successfully created".format(created_profile_name))
    else:
        raise HTTPError('Failed to create the profile for NHC job creation', response=response)
    return created_profile_name


def get_nhc_job_payload(**kwargs):
    """
    This function constructs the payload for NHC job creation

    :param kwargs: request values
    :type kwargs: dict

    :return: nhc_job_payload
    :rtype: dict
    """
    log.logger.debug("Attempting to create payload for NHC job creation request")
    name = kwargs.pop('name')
    time = kwargs.pop("time")
    ne_names = kwargs.pop('ne_elements')
    profile_name = kwargs.get('profile_name')
    ne_type = kwargs.pop('ne_type')

    nhc_job_payload = {"name": name,
                       "description": "",
                       "jobType": "NODE_HEALTH_CHECK",
                       "configurations": [{"neType": ne_type,
                                           "properties": [{"key": "PROFILE_NAME",
                                                           "value": profile_name}]}],
                       "mainSchedule": {"scheduleAttributes": [{"name": "START_DATE",
                                                                "value": time}],
                                        "execMode": "SCHEDULED"},
                       "activitySchedules": [{"platformType": "ECIM",
                                              "value": [{"neType": ne_type,
                                                         "value": [{"activityName": "nodehealthcheck",
                                                                    "execMode": "IMMEDIATE",
                                                                    "order": 1,
                                                                    "scheduleAttributes": []}]}]}],
                       "neNames": ne_names,
                       "collectionNames": [],
                       "savedSearchIds": []}
    log.logger.debug("Successfully created the payload for NHC job creation request")
    return nhc_job_payload


def create_nhc_job(**kwargs):
    """
    This function creates the Node Health Check Job

    :param kwargs: request values
    :type kwargs: dict
    """
    user = kwargs.pop('user')
    profile_name = kwargs.pop('profile_name')
    ne_names = kwargs.pop('ne_elements')
    scheduled_time = kwargs.pop("scheduled_time")
    ne_type = kwargs.pop('ne_type')
    name = kwargs.pop('name')

    report_name = name + "_Report_Administrator_" + scheduled_time.replace('-', '').replace(':', '').replace(" ", '')[:14]
    report_payload = get_nhc_job_payload(name=report_name, time=scheduled_time, ne_elements=ne_names,
                                         profile_name=profile_name, ne_type=ne_type)
    log.logger.debug("Attempting to create job-{}".format(report_name))
    report_response = user.post(NHC_JOB_CREATE_URL, data=json.dumps(report_payload),
                                headers=JSON_SECURITY_REQUEST)
    if not report_response.ok:
        report_response.raise_for_status()
    log.logger.info("NHC job:{0} has been created successfully.".format(report_name))


@retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)), wait_fixed=30,
       stop_max_attempt_number=3)
def get_time_from_enm_return_string_with_gtm_offset(user, time):
    """
    This function gets the time from a server and constructs a time string in format accepted by the NHC end point

    :param user: User to perform the request
    :type user: enmutils.lib.enm_user_2.User
    :param time: required time
    :type time: str

    :return: scheduled_time:
    :rtype: str
    """
    log.logger.debug("Attempting to get and construct the server time for scheduling NHC job")
    response = user.get(GET_TIME_OFFSET_URL, headers=JSON_SECURITY_REQUEST)
    server_time_response = response.json()
    current_server_time = datetime.fromtimestamp(server_time_response['date'] / 1000.0)
    current_server_time_offset = int(round(server_time_response['offset'] / 1000 / 3600))
    new_time = datetime.strptime(time, '%H:%M:%S')
    scheduled_time = current_server_time.replace(hour=new_time.hour, minute=new_time.minute, second=new_time.second,
                                                 microsecond=0)
    scheduled_time = str(scheduled_time) + " GTM+0{}00".format(current_server_time_offset)
    log.logger.debug("Successfully constructed server time for scheduling NHC job")
    return scheduled_time
