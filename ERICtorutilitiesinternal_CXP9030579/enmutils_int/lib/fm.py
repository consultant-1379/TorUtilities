# -*- coding: utf-8 -*-
# ********************************************************************
# Name    : FM
# Summary : Module for interacting with FM application, services in ENM.
#           Allows the user to query FM application in ENM, manage user
#           workspaces, manage alarm routes, generate, and search for
#           alarms in ENM.
# ********************************************************************


import json
import time
import uuid
from datetime import datetime, timedelta
from random import randint
from retrying import retry
from requests.exceptions import HTTPError, ConnectionError

from enmutils.lib import log
from enmutils.lib.enm_user_2 import raise_for_status
from enmutils.lib.exceptions import ScriptEngineResponseValidationError, EnvironError
from enmutils.lib.script_engine_2 import Request

HEADERS = {'Content-Type': 'application/json; charset=utf-8'}
OPEN, HISTORICAL = range(2)
# GET_ERBS_NETWORK_LOGS_ON_NODE = "netlog upload {node_id} SYSTEM_LOG;SHELL_AUDITTRAIL_LOG;CORBA_AUDITTRAIL_LOG;
#                                 CELLO_SECURITYEVENT_LOG;CELLO_AVAILABILITY2_LOG;ALARM_LOG;EVENT_LOG;HW_INVENTORY;
#                                 TROUBLESHOOTING"

GET_ERBS_NETWORK_LOGS_ON_NODE = "netlog upload {node_id} SYSTEM_LOG"
GET_ERBS_NETWORK_LOGS_ON_NODE1 = "netlog upload {node_id} SHELL_AUDITTRAIL_LOG"
GET_ERBS_NETWORK_LOGS_ON_NODE2 = "netlog upload {node_id} CORBA_AUDITTRAIL_LOG"
GET_ERBS_NETWORK_LOGS_ON_NODE3 = "netlog upload {node_id} CELLO_SECURITYEVENT_LOG"
GET_ERBS_NETWORK_LOGS_ON_NODE4 = "netlog upload {node_id} CELLO_AVAILABILITY2_LOG"
GET_ERBS_NETWORK_LOGS_ON_NODE5 = "netlog upload {node_id} ALARM_LOG"
GET_ERBS_NETWORK_LOGS_ON_NODE6 = "netlog upload {node_id} EVENT_LOG"
GET_ERBS_NETWORK_LOGS_ON_NODE7 = "netlog upload {node_id} HW_INVENTORY"
GET_ERBS_NETWORK_LOGS_ON_NODE8 = "netlog upload {node_id} TROUBLESHOOTING"
erbs_netlog = [GET_ERBS_NETWORK_LOGS_ON_NODE, GET_ERBS_NETWORK_LOGS_ON_NODE1, GET_ERBS_NETWORK_LOGS_ON_NODE2,
               GET_ERBS_NETWORK_LOGS_ON_NODE3, GET_ERBS_NETWORK_LOGS_ON_NODE4, GET_ERBS_NETWORK_LOGS_ON_NODE5,
               GET_ERBS_NETWORK_LOGS_ON_NODE6, GET_ERBS_NETWORK_LOGS_ON_NODE7, GET_ERBS_NETWORK_LOGS_ON_NODE8]

# GET_eNodeB_NETWORK_LOGS_ON_NODE = "netlog upload {node_id} AlarmLog;SecurityLog;SwmLog;TnNetworkLog;EsiLog;AvailabilityLog"

GET_eNodeB_NETWORK_LOGS_ON_NODE = "netlog upload {node_id} AlarmLog"
GET_eNodeB_NETWORK_LOGS_ON_NODE1 = "netlog upload {node_id} SecurityLog"
GET_eNodeB_NETWORK_LOGS_ON_NODE2 = "netlog upload {node_id} SwmLog"
GET_eNodeB_NETWORK_LOGS_ON_NODE3 = "netlog upload {node_id} TnNetworkLog"
GET_eNodeB_NETWORK_LOGS_ON_NODE4 = "netlog upload {node_id} EsiLog"
GET_eNodeB_NETWORK_LOGS_ON_NODE5 = "netlog upload {node_id} AvailabilityLog"
eNodeB_netlog = [GET_eNodeB_NETWORK_LOGS_ON_NODE, GET_eNodeB_NETWORK_LOGS_ON_NODE1, GET_eNodeB_NETWORK_LOGS_ON_NODE2,
                 GET_eNodeB_NETWORK_LOGS_ON_NODE3, GET_eNodeB_NETWORK_LOGS_ON_NODE4, GET_eNodeB_NETWORK_LOGS_ON_NODE5]

# GET_SGSN_NETWORK_LOGS_ON_NODE = "netlog upload {node_id} mmi;fm_alarm;fm_event;NodeDump"

GET_SGSN_NETWORK_LOGS_ON_NODE1 = "netlog upload {node_id} mmi"
GET_SGSN_NETWORK_LOGS_ON_NODE2 = "netlog upload {node_id} fm_alarm"
GET_SGSN_NETWORK_LOGS_ON_NODE3 = "netlog upload {node_id} fm_event"
GET_SGSN_NETWORK_LOGS_ON_NODE4 = "netlog upload {node_id} NodeDump"
sgsn_netlog = [GET_SGSN_NETWORK_LOGS_ON_NODE1, GET_SGSN_NETWORK_LOGS_ON_NODE2, GET_SGSN_NETWORK_LOGS_ON_NODE3,
               GET_SGSN_NETWORK_LOGS_ON_NODE4]

# GET_MGW_NETWORK_LOGS_ON_NODE = "netlog upload {0} SYSTEM_LOG;SHELL_AUDITTRAIL_LOG;CORBA_AUDITTRAIL_LOG;CELLO_SECURITYEVENT_LOG;" \
#                               "AVAILABILITY_LOG;ALARM_LOG;EVENT_LOG"

GET_MGW_NETWORK_LOGS_ON_NODE1 = "netlog upload {node_id} SYSTEM_LOG"
GET_MGW_NETWORK_LOGS_ON_NODE2 = "netlog upload {node_id} SHELL_AUDITTRAIL_LOG"
GET_MGW_NETWORK_LOGS_ON_NODE3 = "netlog upload {node_id} CORBA_AUDITTRAIL_LOG"
GET_MGW_NETWORK_LOGS_ON_NODE4 = "netlog upload {node_id} CELLO_SECURITYEVENT_LOG"
GET_MGW_NETWORK_LOGS_ON_NODE5 = "netlog upload {node_id} AVAILABILITY_LOG"
GET_MGW_NETWORK_LOGS_ON_NODE6 = "netlog upload {node_id} ALARM_LOG"
GET_MGW_NETWORK_LOGS_ON_NODE7 = "netlog upload {node_id} EVENT_LOG"
mgw_netlog = [GET_MGW_NETWORK_LOGS_ON_NODE1, GET_MGW_NETWORK_LOGS_ON_NODE2, GET_MGW_NETWORK_LOGS_ON_NODE3,
              GET_MGW_NETWORK_LOGS_ON_NODE4, GET_MGW_NETWORK_LOGS_ON_NODE5, GET_MGW_NETWORK_LOGS_ON_NODE6,
              GET_MGW_NETWORK_LOGS_ON_NODE7]

# fm_09 urls

NODE_GROUP_URL_POST = '/alarmcontroldisplayservice/alarmMonitoring/managed-element-groups/{app}:{user_name}_'\
                      '{operation}Nodes_{group_id}/managedelements'
NODE_GROUP_URL_PUT = '/alarmcontroldisplayservice/alarmMonitoring/managed-element-groups/{app}:{user_name}_'\
                     '{operation}Nodes_{group_id}'
WORKSPACE_URL = "/rest/ui/settings/{ui}/workspace"
SEARCH_OPEN_ALARMS_URL = "/alarmcontroldisplayservice/alarmMonitoring/alarmsearch/openalarms"
SEARCH_HISTORY_ALARMS_URL = "/alarmcontroldisplayservice/alarmMonitoring/alarmsearch/historicalalarms"
SEARCH_EVENT_POIDS_URL = "/alarmcontroldisplayservice/alarmMonitoring/alarmsearch/poidsandheaders"
NODE_SCOPE_URL = "/rest/ui/settings/alarmoverview/nodescope"
SET_HEARTBEAT_URL = "/alarmcontroldisplayservice/alarmMonitoring/alarmoverviewdashboard/subscription/heartbeat/"
ALARM_OVERVIEW_URL = "alarmcontroldisplayservice/alarmMonitoring/alarmoverviewdashboard/group" \
                     "/alarmoverview:nodeselection.%s"
SUBSCRIPTION_URL = "alarmcontroldisplayservice/alarmMonitoring/alarmoverviewdashboard/subscription"
DASH_BOARD_URL = "rest/ui/settings/alarmoverview/dashboard"
NODE_SCOPE_PAYLOAD = {"id": None,
                      "value": '{"groupName":"alarmoverview:nodeselection.%s",'
                               '"selectedGroupName":%s,'
                               '"selectedCount":%s,'
                               '"totalCount":%s,'
                               '"isShown":true}'}
ALARM_TEXT_ROUTING_URL = "alarmcontroldisplayservice/alarmMonitoring/alarmtextrouting/"


def alarm_overview_home(user):
    """
    Visit the alarm monitor home page
    :param user: ENM user instance
    :type user: enmutils.lib.enm_user_2.User
    """
    home_url = '/#alarmoverview'
    response = user.get(home_url, verify=False)
    raise_for_status(response, message_prefix="Failed to get alarm monitor home: ")


def enable_alarm_supervision(user, nodes):
    """
    Enables the alarm supervision in ENM for the given nodes
    :param user: ENM user instance
    :type user: enmutils.lib.enm_user_2.User
    :param nodes: list of enmutils.lib.enm_node.Node instances to be used with this request
    :type nodes: list
    """
    url = "/alarmcontroldisplayservice/alarmMonitoring/alarmoperations/nodeactions"

    user_data = {
        "action": "supervision",
        "nodes": ';'.join([node.node_id for node in nodes]),
        "operatorName": "administrator",
        "value": "ON"
    }
    response = user.post(url, data=json.dumps(user_data), headers=HEADERS)
    raise_for_status(response, message_prefix="Failed to enable alarm supervision: ")


def initiate_alarm_sync(user, nodes):
    """
    Initiates the alarm sync for the given nodesraise_for_status(response, message_prefix="Failed to enable alarm supervision: ")
    :param user: ENM user instance
    :type user: enmutils.lib.enm_user_2.User
    :param nodes: list of enmutils.lib.enm_node.Node instances to be used with this request
    :type nodes: list
    """
    url = "/alarmcontroldisplayservice/alarmMonitoring/alarmoperations/nodeactions"

    user_data = {
        "action": "sync",
        "nodes": ';'.join([node.node_id for node in nodes]),
        "operatorName": "administrator",
        "value": True
    }
    response = user.post(url, data=json.dumps(user_data), headers=HEADERS)
    raise_for_status(response, message_prefix="Failed to initiate alarm sync: ")


@retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)), wait_fixed=120000,
       stop_max_attempt_number=2)
def acknowledge_alarms(user, nodes, num_alarms=10):
    """
    Acknowledges the alarms in ENM for the given nodes
    :param user: ENM user instance
    :type user: enmutils.lib.enm_user_2.User
    :param nodes: list of enmutils.lib.enm_node.Node instances to be used with this request
    :type nodes: list
    :param num_alarms: Number of alarms to be acknowledged
    :type num_alarms: int
    """
    alarms_json = {}
    alarms = _fetch_alarms(user, nodes)
    try:
        alarms_json = alarms.json()[1]
    except IndexError:
        log.logger.debug('Unable to fetch alarms from the json file as required index is not present in the list')
    if 'eventPoIds' not in alarms_json:
        log.logger.debug("No alarms in the json response, returning to called function")
        return
    alarms_poids = [str(alarm) for alarm in alarms_json['eventPoIds'][:num_alarms] if alarms_json]
    log.logger.info("Number of alarm PoIds fetched : {0}".format(len(alarms_poids)))
    url = "/alarmcontroldisplayservice/alarmMonitoring/alarmoperations/nodeactions"
    user_data = {
        "action": "ACK",
        "alarmIdList": ",".join(alarms_poids),
        "operatorName": "administrator",
        "value": "true"
    }
    response = user.post(url, data=json.dumps(user_data), headers=HEADERS)
    log.logger.debug("Response status code : {0} and response text : {1}".format(response.status_code, response.text))
    raise_for_status(response, message_prefix="Failed to acknowledge alarms: ")


def network_explorer_search_for_nodes(user):
    """
    Visits the network explorer to search for the nodes
    :param user: ENM user instance
    :type user: enmutils.lib.enm_user_2.User
    """
    network_explorer_url = '/#networkexplorer?returnType=multipleObjects'
    network_element_search_url = '/#networkexplorer/search/NetworkElement?page=1&size=50&returnType=multipleObjects'

    user.get(network_explorer_url, verify=False)
    search_response = user.get(network_element_search_url, verify=False)
    raise_for_status(search_response, message_prefix="Failed to search for nodes in netex: ")


def alarm_overview(user, sleep=60, heart_beat_refresh_time=10):
    """
    View the alarm monitor and keep on receiving the alarms to simulate the browser
    :param user: ENM user instance
    :type user: enmutils.lib.enm_user_2.User
    :param sleep: time in seconds you want the gui to remain open by the user
    :type sleep: int
    :param heart_beat_refresh_time: Interval in seconds between doing get for all alarms
    :type heart_beat_refresh_time: float
    """
    timeout = datetime.now() + timedelta(seconds=sleep)
    while datetime.now() < timeout:
        response = user.post(SET_HEARTBEAT_URL + str(uuid.uuid4()), headers=HEADERS)
        log.logger.info("POST method response: {0}".format(str(response)))
        time.sleep(heart_beat_refresh_time)


def _fetch_alarms(user, nodes):
    """
    Returns 1000 alarm records on the given nodes
    :param user: ENM user instance
    :type user: enmutils.lib.enm_user_2.User
    :param nodes: list of enmutils.lib.enm_node.Node instances to be used with this request
    :type nodes: list
    :return: alarm ack response
    :rtype: requests.Response
    """
    event_poid_url = '/alarmcontroldisplayservice/alarmMonitoring/alarmoperations/eventpoids'
    node_ids = [node.node_id for node in nodes]
    log.logger.info("Number of nodes on which alarms will be fetched : {0}".format(len(node_ids)))
    poid_data = {
        "filters": "",
        "category": "All",
        "nodes": ";".join(node_ids),
        "recordLimit": 1000,
        "tableSettings": "fdn#true#false,presentSeverity#true#false,specificProblem#true#false,eventTime#true#false,recordType#true#false,alarmingObject#false#false,insertTime#false#false,probableCause#true#false,eventType#true#false,problemText#false#false,problemDetail#false#false,objectOfReference#false#false,commentText#false#false,ackOperator#false#false,ackTime#false#false,ceaseOperator#false#false,ceaseTime#false#false,repeatCount#false#false,oscillationCount#false#false,trendIndication#false#false,previousSeverity#false#false,alarmState#false#false,alarmNumber#false#false,backupStatus#false#false,backupObjectInstance#false#false,proposedRepairAction#false#false,fmxGenerated#false#false,processingType#false#false,root#false#false",
        "timestamp": time.mktime(datetime.now().timetuple()) * 1000,
        "sortCriteria": [{"attribute": "insertTime", "mode": "desc"}]
    }
    response = user.post(event_poid_url, data=json.dumps(poid_data), verify=False, headers=HEADERS)
    raise_for_status(response, message_prefix="Failed to retrieve alarms from ENM: ")
    return response


def alarmviewer_help(user):
    """
    Browse the arlam viewer help page
    :param user: ENM user instance
    :type user: enmutils.lib.enm_user_2.User
    """
    user.get('/#help/app/alarmviewer')
    user.get('/#help/app/alarmviewer/concept/ui')
    user.get('/#help/app/alarmviewer/concept/tutorials/AlarmOperations')
    user.get('/#help/app/alarmviewer/concept/tutorials/Filters')


def create_empty_workspaces_for_given_users(users, app):
    """
    Creates empty workspaces for the given users, either for alarm monitor or alarm search
    :param users: Users for whom the empty workspace is to be created
    :type users: list
    :param app: Name of the application (supports only alarm monitor or alarm search)
    :type app: str
    :return: ENM username as key and workspace ID, nodegroup ID tuple as value
    :rtype: dict
    """
    user_workspace_dict = {}
    for user in users:
        workspace_id, node_group_id = create_empty_workspace_for_a_user(user, app)
        user_workspace_dict[user.username] = (workspace_id, node_group_id)
        time.sleep(1)
    return user_workspace_dict


@retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)), wait_fixed=60000, stop_max_attempt_number=2)
def create_empty_workspace_for_a_user(user, app):
    """
    Creates empty workspace for a single ENM user
    :param user: User for whom the empty workspace is to be created
    :type user: enmutils.lib.enm_user_2.User
    :param app: Name of the application (supports only alarm monitor or alarm search)
    :type app: str
    :return: workspace ID and node group ID
    :rtype: tuple
    """
    node_group_id = randint(1000000000000, 9999999999999)
    workspace_id = randint(1000000000000, 9999999999999)
    log.logger.info("Creating an empty workspace for app : {0}, user : {1} with workspace_id : {2} and "
                    " node_group_id : {3}.".format(app, user.username, workspace_id, node_group_id))

    user.put(NODE_GROUP_URL_PUT.format(app=app, user_name=user.username, operation='imported', group_id=node_group_id),
             headers=HEADERS)
    time.sleep(2)
    user.put(NODE_GROUP_URL_PUT.format(app=app, user_name=user.username, operation='selected', group_id=node_group_id),
             headers=HEADERS)

    workspace_payload = generate_payload_for_workspace(workspace_id=workspace_id,
                                                       number_of_nodes=0,
                                                       user_name=user.username,
                                                       group_id=node_group_id,
                                                       date=str(int(round(time.time() * 1000))),
                                                       app=app)
    time.sleep(2)
    ui_name = 'alarmmonitor' if app == "alarmviewer" else app
    user.put(WORKSPACE_URL.format(ui=ui_name), data=json.dumps(workspace_payload), headers=HEADERS)
    return workspace_id, node_group_id


def generate_payload_for_workspace(workspace_id, number_of_nodes, user_name, group_id, date, app):
    """
    Function to create a payload body for alarm monito or alarm search workspace
    :param workspace_id: ID of the users workspace
    :type workspace_id: int
    :param number_of_nodes: number of nodes to be added to the workspace
    :type number_of_nodes: int
    :param user_name: name of the user
    :type user_name: str
    :param group_id: Id of the node group
    :type group_id: int
    :param date: date in epoch
    :type date: str
    :param app:To check whether alarm monitor or alarm search
    :type app: str
    :return: workspace payload body
    :rtype: dict
    """
    if app == "alarmviewer":
        data = {"id": "workspace_%s" % workspace_id,
                "value": '{"topology":true,"nodesImported":%s,"id":"workspace_%s",'
                         '"groupName":"alarmviewer:%s_importedNodes_%s;alarmviewer:%s_selectedNodes_%s",'
                         '"date":%s,"workspaceName":"Workspace%s"}' % (number_of_nodes, workspace_id, user_name, group_id,
                                                                       user_name, group_id, date, workspace_id)}
    else:
        data = {"id": "workspace_%s" % workspace_id,
                "value": '{"search":true,"nodesImported":%s,"id":"workspace_%s",'
                         '"groupName":"alarmsearch:%s_importedNodes_%s;alarmsearch:%s_selectedNodes_%s",'
                         '"date":%s,"workspaceName":"Workspace%s"}' % (number_of_nodes, workspace_id, user_name, group_id,
                                                                       user_name, group_id, date, workspace_id)}
    return data


@retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)), wait_fixed=120000, stop_max_attempt_number=2)
def add_nodes_to_given_workspace_for_a_user(user, node_data, workspace_id, node_group_id, node_count, app):
    """
    Function to populate nodes to alarm search workspaces for a user
    :param user: User to create the workspaces
    :type user: enmutils.lib.enm_user_2.User
    :param node_data: Dict of nodes with action type and uid
    :type node_data: dict
    :param workspace_id: Workspace id of the user
    :type workspace_id: int
    :param node_group_id: Node group id of the user
    :type node_group_id: int
    :param node_count: Count of the nodes
    :type node_count: int
    :param app: UI application name
    :type app: str
    """
    time.sleep(randint(1, 60))
    log.logger.info("Updating workspace for {0} with user {1}, for nodes {2}".format(app, user.username, node_count))

    node_data["uId"] = str(uuid.uuid4())
    user.post(NODE_GROUP_URL_POST.format(app=app, user_name=user.username, operation='imported', group_id=node_group_id),
              data=json.dumps(node_data), headers=HEADERS)

    time.sleep(2)

    node_data["uId"] = str(uuid.uuid4())
    user.post(NODE_GROUP_URL_POST.format(app=app, user_name=user.username, operation='selected', group_id=node_group_id),
              data=json.dumps(node_data), headers=HEADERS)
    workspace_payload = generate_payload_for_workspace(workspace_id=workspace_id,
                                                       number_of_nodes=node_count,
                                                       user_name=user.username,
                                                       group_id=node_group_id,
                                                       date=str(int(round(time.time() * 1000))),
                                                       app=app)
    time.sleep(2)
    ui_name = 'alarmmonitor' if app == "alarmviewer" else app
    user.put(WORKSPACE_URL.format(ui=ui_name), data=json.dumps(workspace_payload), headers=HEADERS)


@retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)), wait_fixed=120000, stop_max_attempt_number=2)
def delete_nodes_from_a_given_workspace_for_a_user(user, node_data, workspace_id, node_group_id, app):
    """
    Function to delete nodes from alarm monitor workspaces for a user
    :param user: User to create the workspaces
    :type user: enmutils.lib.enm_user_2.User
    :param node_data: Dict of nodes with action type and uid
    :type node_data: dict
    :param workspace_id: Workspace id of the user
    :type workspace_id: int
    :param node_group_id: Node group id of the user
    :type node_group_id: int
    :param app: UI application name
    :type app: str
    """
    time.sleep(randint(1, 60))
    log.logger.info("Deleting nodes from {0} workspace for user {1}".format(app, user.username))

    user.post(NODE_GROUP_URL_POST.format(app=app, user_name=user.username, operation='selected', group_id=node_group_id),
              data=json.dumps(node_data), headers=HEADERS)

    node_data["uId"] = str(uuid.uuid4())

    time.sleep(2)

    user.post(NODE_GROUP_URL_POST.format(app=app, user_name=user.username, operation='imported', group_id=node_group_id),
              data=json.dumps(node_data), headers=HEADERS)

    workspace_payload = generate_payload_for_workspace(workspace_id=workspace_id,
                                                       number_of_nodes=0,
                                                       user_name=user.username,
                                                       group_id=node_group_id,
                                                       date=str(int(round(time.time() * 1000))),
                                                       app=app)
    time.sleep(2)
    ui_name = 'alarmmonitor' if app == "alarmviewer" else app
    user.put(WORKSPACE_URL.format(ui=ui_name), data=json.dumps(workspace_payload), headers=HEADERS)


@retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)), wait_fixed=120000, stop_max_attempt_number=2)
def alarm_search_for_open_alarms(user, nodes, from_datetime, to_datetime, search_type, num_alarms=100):
    """
    Search for the open alarms using the nodes with the datetime criteria
    :param user: ENM user instance
    :type user: enmutils.lib.enm_user_2.User
    :param nodes: list of enmutils.lib.enm_node.Node instances to be used with this request
    :type nodes: list
    :param from_datetime: date to search from
    :type from_datetime: int
    :param to_datetime: date to search to
    :type to_datetime: int
    :param search_type: indicates if the search is performed on the open or historical alarms
    :type search_type: str
    :param num_alarms: number of alarms to search
    :type num_alarms: int
    """
    alarms_json = {}
    response = fetch_response_for_given_search_type(user, nodes, from_datetime, to_datetime, search_type)
    try:
        alarms_json = response.json()[2] if response else {}
    except (IndexError, ValueError) as e:
        log.logger.info('Unable to fetch alarms from the json file, raised Exception : {0}'.format(e))
        return
    if not alarms_json['poIds']:
        log.logger.info("No open alarms found for the given time period")
        return

    alarms_poids = [str(alarm) for alarm in alarms_json['poIds'][:num_alarms] if search_type == OPEN]

    search_data = {
        "eventPoIds": alarms_poids,
        "tableSettings": "fdn#true#false,alarmingObject#false#false,presentSeverity#true#false,eventTime#true#false,insertTime#false#false,specificProblem#true#false,probableCause#false#false,eventType#false#false,recordType#false#false,problemText#false#false,problemDetail#false#false,objectOfReference#false#false,commentText#false#false,ackOperator#false#false,ackTime#false#false,ceaseOperator#false#false,ceaseTime#false#false,repeatCount#false#false,oscillationCount#false#false,trendIndication#false#false,previousSeverity#false#false,alarmState#false#false,alarmNumber#false#false,backupStatus#false#false,backupObjectInstance#false#false,proposedRepairAction#false#false,fmxGenerated#false#false,processingType#false#false,eventPoIdAsString#false#false,root#false#false"
    }
    response = user.post(SEARCH_OPEN_ALARMS_URL, data=json.dumps(search_data), headers=HEADERS)
    raise_for_status(response)
    log.logger.info("Alarm search completed")


@retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)), wait_fixed=120000, stop_max_attempt_number=2)
def alarm_search_for_historical_alarms(user, nodes, from_datetime, to_datetime, search_type,
                                       attribute="presentSeverity¡¿§CRITICAL¡¿§=§¿¡recordType¡¿§ALARM¡¿§="):
    """
    Search for the historical alarms using the nodes with the datetime and attribute filter criteria
    :param user: ENM user instance
    :type user: enmutils.lib.enm_user_2.User
    :param nodes: list of enmutils.lib.enm_node.Node instances to be used with this request
    :type nodes: list
    :param from_datetime: date to search from
    :type from_datetime: int
    :param to_datetime: date to search to
    :type to_datetime: int
    :param search_type: indicates if the search is performed on the open or historical alarms
    :type search_type: str
    :param attribute: Used to filter the search results based on the given attribute
    :type attribute: str
    """
    response = fetch_response_for_given_search_type(user, nodes, from_datetime, to_datetime, search_type, attribute)
    raise_for_status(response)


@retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)), wait_fixed=120000, stop_max_attempt_number=2)
def fetch_response_for_given_search_type(user, nodes, from_date=None, to_date=None, search_type=OPEN, attribute=""):
    """
    Returns 1000 alarm records on the given nodes
    :param user: ENM user instance
    :type user: enmutils.lib.enm_user_2.User
    :param nodes: list of enmutils.lib.enm_node.Node instances to be used with this request
    :type nodes: list
    :param from_date : Date to search from
    :type from_date: int
    :param to_date: Till the date
    :type to_date: int
    :param attribute: Used to filter the search results based on the given attribute
    :type attribute: str
    :param search_type: indicates if the search is performed on the open or historical alarms
    :type search_type: str
    :return: alarm ack response
    :rtype: requests.Response
    """
    url = SEARCH_EVENT_POIDS_URL if search_type == OPEN else SEARCH_HISTORY_ALARMS_URL
    node_ids = [node.node_id for node in nodes]
    log.logger.info("Number of nodes on which alarms will be fetched : {0}".format(len(node_ids)))
    poid_data = {
        "nodes": ';'.join(node_ids),
        "fromDate": str(from_date),
        "toDate": str(to_date),
        "alarmAttributes": attribute,
        "tableSettings": "fdn#true#false,alarmingObject#false#false,presentSeverity#true#false,eventTime#true#false,insertTime#false#false,specificProblem#true#false,probableCause#false#false,eventType#false#false,recordType#false#false,problemText#false#false,problemDetail#false#false,objectOfReference#false#false,commentText#false#false,ackOperator#false#false,ackTime#false#false,ceaseOperator#false#false,ceaseTime#false#false,repeatCount#false#false,oscillationCount#false#false,trendIndication#false#false,previousSeverity#false#false,alarmState#false#false,alarmNumber#false#false,backupStatus#false#false,backupObjectInstance#false#false,proposedRepairAction#false#false,fmxGenerated#false#false,processingType#false#false,eventPoIdAsString#false#false,root#false#false",
        "sortCriteria": [{"attribute": "insertTime", "mode": "desc"}]
    }
    response = user.post(url, data=json.dumps(poid_data), headers=HEADERS)
    raise_for_status(response, message_prefix="Failed to retrieve alarms from ENM: ")
    return response


def create_workspace_payload(workspace_id, number_of_nodes, user_name, group_id, date):
    """
    Function to create a payload boady for alarm monitor workspace
    :param workspace_id: Id of the users workspace
    :type workspace_id: int
    :param number_of_nodes:
    :type number_of_nodes: int
    :param user_name: name of the user
    :type user_name: str
    :param group_id: Id of the node group
    :type group_id: int
    :param date: date in epoch
    :type date: int
    :return: workspace payload body
    :rtype: dict
    """

    data = {"id": "workspace_%s" % workspace_id,
            "value": '{"topology":true,"nodesImported":%s,"id":"workspace_%s",'
                     '"groupName":"alarmviewer:%s_importedNodes_%s;alarmviewer:%s_selectedNodes_%s",'
                     '"date":%s,"workspaceName":"Workspace%s"}' % (number_of_nodes, workspace_id, user_name, group_id,
                                                                   user_name, group_id, date, workspace_id)}
    return data


def create_dashboard_items(node_scope_id, number_of_nodes, user, workspace_id):
    """
    Function populate alarm overview dashboards with widgets
    :param node_scope_id: Id of the node scope
    :type node_scope_id: int
    :param number_of_nodes: Number of nodes
    :type number_of_nodes: int
    :param user: User to execute tasks
    :type user: enmutils.lib.enm_user_2.User
    :param workspace_id: Id of the workspace
    :type workspace_id: int
    """
    put_to_dashboard_payload = {"id": None,
                                "value": '{"type":"Dashboard",'
                                         '"layout":"one-column",'
                                         '"items":[[%s]],'
                                         '"emptyDashboardText":"Add a widget to display it here",'
                                         '"workspaceName":"Workspace %s","date":%s}'}
    widgets = [
        '{"header":"Most Problematic Node By Alarm Count","type":"NodeRankingByAlarmCount","maximizable":false,'
        '"closable":true,"maximizeText":"Maximize","minimizeText":"Minimize","closeText":"Close","settings":true,'
        '"config":{"isDashboard":true,"settings":true,"maximizable":true,'
        '"groupName":"alarmoverview:nodeselection.%s","count":20}}' % node_scope_id,

        '{"header":"Alarm Severity Summary","type":"AlarmSeveritySummary","maximizable":false,"closable":true,'
        '"maximizeText":"Maximize","minimizeText":"Minimize","closeText":"Close","settings":true,'
        '"config":{"isDashboard":true,"settings":true,"maximizable":true,'
        '"groupName":"alarmoverview:nodeselection.%s","severity":["CRITICAL","MAJOR","MINOR","WARNING",'
        '"INDETERMINATE","CLEARED"]}}' % node_scope_id,

        '{"header":"Most Problematic Alarm Type By Count","type":"AlarmTypeRanking","maximizable":false,'
        '"closable":true,"maximizeText":"Maximize","minimizeText":"Minimize","closeText":"Close",'
        '"settings":true,"config":{"isDashboard":true,"settings":true,"maximizable":true,'
        '"groupName":"alarmoverview:nodeselection.%s","count":10}}' % node_scope_id,

        '{"header":"Alarm Type Summary","type":"AlarmTypeSummary","maximizable":false,"closable":true,'
        '"maximizeText":"Maximize","minimizeText":"Minimize","closeText":"Close","settings":true,'
        '"config":{"isDashboard":true,"settings":true,"maximizable":true,'
        '"groupName":"alarmoverview:nodeselection.%s",'
        '"alarmType":["Heartbeat Failure","SP: Node is on fire","SP: Node is on flood",'
        '"FEATURERESOURCEMISSING","CPU busy threshold exceeded"]}}' % node_scope_id
    ]

    for widget in widgets:
        subscription_payload = {"groupName": "alarmoverview:nodeselection.%s" % node_scope_id,
                                "widgetAttributes": {"widgetName": widget,
                                                     "configuration": {"count": number_of_nodes}}}

        user.post(SUBSCRIPTION_URL, data=json.dumps(subscription_payload), headers=HEADERS)

    data = put_to_dashboard_payload.copy()
    data['id'] = "workspace_%s" % workspace_id
    data['value'] = data['value'] % (",".join([widget for widget in widgets]),
                                     workspace_id, str(int(round(time.time() * 1000))))
    user.put(DASH_BOARD_URL, data=json.dumps(data), headers=HEADERS)


def create_alarm_overview_dashboards(users, nodes):
    """
    Function to create and populate alarm overview dashboards for each user
    :param users: Users to execute tasks
    :type users: list
    :param nodes: Nodes
    :type nodes: list
    """
    poids = [node.poid for node in nodes]

    for user in users:
        create_dashboard_for_a_user(user, poids)
        log.logger.debug("Waiting for 10 seconds before creating next user dashboard.")
        time.sleep(10)


@retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)),
       wait_fixed=30000, stop_max_attempt_number=3)
def create_dashboard_for_a_user(user, poids):
    """
    Function to create and populate alarm overview dashboards for a user
    :param user: User to execute task
    :type user: enmutils.lib.enm_user_2.User
    :param poids: List of node poids
    :type poids: list
    """
    log.logger.info("Creating an Alarm Overview dashboard for user {} .".format(user.username))
    workspace_id = randint(1000000000000, 9999999999999)
    node_scope_id = "{}.{}.{}".format(randint(100, 999), randint(100000, 999999), int(round(time.time())))

    # put empty node scope
    data = NODE_SCOPE_PAYLOAD.copy()
    data['value'] = data['value'] % (node_scope_id, '""', 0, 0)
    data['id'] = "workspace_%s" % workspace_id
    user.put(NODE_SCOPE_URL, data=json.dumps(data), headers=HEADERS)

    # add nodes to the node scope
    data = {"moList": [node for node in poids], "uId": str(uuid.uuid4())}
    user.post(ALARM_OVERVIEW_URL % node_scope_id, data=json.dumps(data), headers=HEADERS)

    # put node scope do dashboard
    create_dashboard_items(node_scope_id, len(poids), user, workspace_id)

    # update node scope
    data = NODE_SCOPE_PAYLOAD.copy()
    data['value'] = data['value'] % (node_scope_id, '""', 0, int(len(poids)))
    data['id'] = "workspace_%s" % workspace_id
    user.put(NODE_SCOPE_URL, data=json.dumps(data), headers=HEADERS)


def alarmsearch_help(user):
    """
    Browse the alarm search help pages
    :param user: ENM user instance
    :type user: enmutils.lib.enm_user_2.User
    """

    user.get('/#help/app/alarmsearch')
    user.get('/#help/app/alarmsearch/concept/tutorials/map')
    user.get('/#help/app/alarmsearch/concept/ui')


def collect_erbs_network_logs(user, node):
    """
    Collecting a number of network logs  on a given node
    :param user: ENM user instance
    :type user: enmutils.lib.enm_user_2.User
    :param node: ENM node instance
    :type node: enmutils.lib.enm_node.Node
    :rtype: list
    :return: netlogs for a given node
    :raises ScriptEngineResponseValidationError: If there is no output after executing the request
    """
    for netlog in erbs_netlog:
        request = Request(netlog.format(node_id=node.node_id), user=user, timeout=1200)
        response = request.execute()
        time.sleep(2)
        output = response.get_output()[1:]

        if not output:
            log.logger.debug("NO OUTPUT, response: {}".format(response.json))
            raise ScriptEngineResponseValidationError("No output received. Response: {}".format(response.json),
                                                      response=response)
    return output


def collect_eNodeB_network_logs(user, node):
    """
    Collecting a number of network logs  on a given node
    :param user: ENM user instance
    :type user: enmutils.lib.enm_user_2.User
    :param node: ENM node instance
    :type node: enmutils.lib.enm_node.Node
    :rtype: list
    :return: netlogs for a given node
    :raises ScriptEngineResponseValidationError: If there is no output after executing the request
    """
    for netlog in eNodeB_netlog:
        request = Request(netlog.format(node_id=node.node_id), user=user, timeout=1200)
        response = request.execute()
        output = response.get_output()[1:]

        if not output:
            log.logger.debug("NO OUTPUT, response: {}".format(response.json))
            raise ScriptEngineResponseValidationError("No output received. Response: {}".format(response.json),
                                                      response=response)
    return output


def collect_sgsn_network_logs(user, node):
    """
    Collecting a number of network logs  on a given node
    :param user: ENM user instance
    :type user: enmutils.lib.enm_user_2.User
    :param node: ENM node instance
    :type node: enmutils.lib.enm_node.Node
    :rtype: list
    :return: netlogs for a given node
    :raises ScriptEngineResponseValidationError: If there is no output after executing the request
    """
    for netlog in sgsn_netlog:
        request = Request(netlog.format(node_id=node.node_id), user=user, timeout=1200)
        response = request.execute()
        time.sleep(2)
        output = response.get_output()[1:]

        if not output:
            log.logger.debug("NO OUTPUT, response: {}".format(response.json))
            raise ScriptEngineResponseValidationError("No output received. Response: {}".format(response.json),
                                                      response=response)
    return output


def collect_mgw_network_logs(user, node):
    """
    Collecting a number of network logs  on a given node
    :param user: ENM user instance
    :type user: enmutils.lib.enm_user_2.User
    :param node: ENM node instance
    :type node: enmutils.lib.enm_node.Node
    :rtype: list
    :return: netlogs for a given node
    :raises ScriptEngineResponseValidationError: If there is no output after executing the request
    """
    for netlog in mgw_netlog:
        request = Request(netlog.format(node_id=node.node_id), user=user, timeout=1200)
        response = request.execute()
        time.sleep(2)
        output = response.get_output()[1:]

        if not output:
            log.logger.debug("NO OUTPUT, response: {}".format(response.json))
            raise ScriptEngineResponseValidationError("No output received. Response: {}".format(response.json),
                                                      response=response)
    return output


def get_alarm_hist(time_period_in_min, user):
    """
    This function executes the Alarm History command on the cli
    :param time_period_in_min: Alarm search time period
    :type time_period_in_min: int
    :param user: ENM user instance
    :type user: enmutils.lib.enm_user_2.User
    :returns: alarm history output on all nodes present in the deployment
    :rtype: enmutils.lib.script_engine_2.Response
    :raises ScriptEngineResponseValidationError: If there is no output after executing the request
    """

    seconds = time.sleep(randint(1, 60))
    log.logger.debug("Sleeping for {0}s".format(seconds))
    present_time = datetime.now()
    time_span = present_time - timedelta(minutes=time_period_in_min)
    alarm_search_time = time_span.strftime('%Y-%m-%dT%H:%M:%S')
    get_alarm_history_for_all_nodes = 'alarm hist * --begin {0}'.format(alarm_search_time)
    log.logger.debug('Run the following command {0}'.format(get_alarm_history_for_all_nodes))
    response = user.enm_execute(get_alarm_history_for_all_nodes)
    output = response.get_output()[1:]
    log.logger.debug("Output is: {0}".format(output))

    if not output:
        log.logger.debug("NO OUTPUT, response: {}".format(response.json()))
        raise ScriptEngineResponseValidationError("No output received. Response: {}".format(response.json()),
                                                  response=response)

    return output


@retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)), wait_fixed=60000,
       stop_max_attempt_number=3)
def get_list_of_routing_policies_poids(user):
    """
    Returns number of existing routing policies on the system.
    :param user: User to perform request
    :type user: enmutils.lib.enm_user_2.User
    :return: Number of existing policies
    :rtype: int
    :raises EnvironError: When json in not present in a successful response
    """
    log.logger.debug("Retrieving a list of routing policies present on the system.")
    response = user.post(ALARM_TEXT_ROUTING_URL + "policieslist",
                         data=json.dumps({"sortAttribute": "createdTime", "sortMode": "desc"}), headers=HEADERS)
    response.raise_for_status()
    if response.status_code == 200 and response.json():
        poids = [item["routeIdAsString"] for item in response.json()[1]["poIds"]]
    else:
        raise EnvironError("Post Request to '{}' returned no json".format(ALARM_TEXT_ROUTING_URL + "policieslist"))

    log.logger.debug("Policies list successfully retrieved")
    return poids


@retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)), wait_fixed=60000,
       stop_max_attempt_number=3)
def get_routing_policy_poid_by_name(user, poids, name):
    """
    Returns number of existing routing policies on the system.
    :param user: User to perform request
    :type user: enmutils.lib.enm_user_2.User
    :param poids: List of poids
    :type poids: list
    :param name: Name to search for
    :type name: str
    :return: Number of existing policies
    :rtype: int
    :raises EnvironError: When json in not present in a successful response
    """
    route_id = ""
    log.logger.debug("Retrieving poid of {}".format(name))
    response = user.post(ALARM_TEXT_ROUTING_URL + "policyListBasedOnBatches",
                         data=json.dumps({"alarmRouteIds": ";".join(poids)}), headers=HEADERS)
    response.raise_for_status()
    if response.status_code == 200 and response.json():
        for item in response.json():
            if item['fileName'] == name:
                route_id = item["routeIdAsString"]
    else:
        raise EnvironError(
            "Post Request to '{}' returned no json".format(ALARM_TEXT_ROUTING_URL + "policyListBasedOnBatches"))

    log.logger.debug("Poid of {} successfully retrieved".format(name))

    return route_id


class FmAlarmRoute(object):
    """
    Object representing a FM Routing Policy saved to file
    """
    ALARM_TEXT_ROUTING_URL = "alarmcontroldisplayservice/alarmMonitoring/alarmtextrouting/"

    def __init__(self, user, nodes_list, file_name, route_name, description="", file_headers=None):
        """
        FmAlarmRoute constructor
        :param user: User to perform requests
        :type user: enmutils.lib.enm_user_2.User
        :param nodes_list: list of node objects
        :type nodes_list: list
        :param file_name: Name of the file to which routing will be saved
        :type file_name: str
        :param route_name: Name of the Routing Policy
        :type route_name: str
        :param description: Description to be added
        :type description: str
        :param file_headers: List of attributes of the Routing File
        :type file_headers: list
        """
        self.user = user
        self.nodes_list = nodes_list
        self.file_name = file_name
        self.route_name = route_name
        self.description = description
        self.id = None
        self.file_headers = file_headers

    def _prepare_fdn_list_string(self, nodes_list):
        """
        Concatenates a string with needed for the payload
        :param nodes_list: list of node objects
        :type nodes_list: list
        :return: node fndns and node types
        :rtype: tuple
        """
        nodes = {}
        ne_fdns = ""
        node_types = ""

        for node in nodes_list:
            if node.primary_type not in nodes.keys():
                nodes[node.primary_type] = [node.node_id]
            else:
                nodes[node.primary_type].append(node.node_id)

        for node_type in nodes.keys():
            fdns = ",".join([fdn for fdn in nodes[node_type]])
            ne_fdns += node_type + "#" + fdns + ";"
            node_types += node_type + ","

        return ne_fdns, node_types

    def _create_request_payload(self, nodes_list, file_name, route_name, description):
        """
        Created a payload needed to for Routing Policy creation
        :param nodes_list: List of node object to be add to the Routing Policy
        :type nodes_list: list
        :param file_name: Name of the file to which routing will be saved
        :type file_name: str
        :param route_name: Name of the Routing Policy
        :type route_name: str
        :param description: Description to be added
        :type description: str
        :return: Request payload
        :rtype: dict
        """
        log.logger.debug("Adding nodes to the create request payload.")

        headers = ['fdn', 'alarmingObject', 'presentSeverity', 'eventTime', 'insertTime', 'specificProblem',
                   'probableCause', 'eventType', 'objectOfReference', 'commentText', 'repeatCount', 'alarmState']

        ne_fdns, node_types = self._prepare_fdn_list_string(nodes_list)
        payload = {'description': description,
                   'enablePolicy': True,
                   'fileHeaders': self.file_headers if self.file_headers else headers,
                   'fileName': file_name,
                   'fileType': 'TXT',
                   'name': route_name,
                   'neFdn': ne_fdns,
                   'neType': node_types,
                   'outputType': 'file',
                   'routeType': 'FILE',
                   'subordinateType': 'All_SUBORDINATES'}

        log.logger.debug("Payload successfully created.")
        return payload

    @retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)), wait_fixed=60000,
           stop_max_attempt_number=3)
    def create(self):
        """
        Creates a routing policy
        """
        log.logger.info("Creating Routing Policy {}".format(self.file_name))
        payload = self._create_request_payload(self.nodes_list, self.file_name, self.route_name, self.description)
        response = self.user.post(self.ALARM_TEXT_ROUTING_URL + "createRoute", data=json.dumps(payload),
                                  headers=HEADERS)
        response.raise_for_status()

        self._get_the_route_id(self.file_name)

    @retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)), wait_fixed=60000,
           stop_max_attempt_number=3)
    def delete(self):
        """
        Deletes a Routing Policy
        """
        self.user.post(self.ALARM_TEXT_ROUTING_URL + "deletePolicies", data=json.dumps({"alarmRouteIds": self.id}),
                       headers=HEADERS)

    @retry(retry_on_exception=lambda e: isinstance(e, (HTTPError, ConnectionError)), wait_fixed=60000,
           stop_max_attempt_number=3)
    def _get_the_route_id(self, name):
        """
        Retrieves poid of a created Routing Policy needed for deletion
        :param name: Name of the Routing Policy
        :type name: str
        :raises EnvironError: When get routing policies returns no poids or policy with given name cannot be found
        """
        log.logger.debug("Retrieving the Route ID.")
        poids = get_list_of_routing_policies_poids(self.user)

        if poids:
            route_id = get_routing_policy_poid_by_name(self.user, poids, name)
            if route_id:
                self.id = route_id
            else:
                raise EnvironError("Profile could not retrieve ID of the list policy")
        else:
            raise EnvironError("Profile could not retrieve list of routing policies")
        log.logger.debug("Route Id retrieved.")

    def _teardown(self):
        """
        Function to delete created policies on the profile termination.
        """
        log.logger.debug("Tearing down alarm route {0}".format(self.file_name))
        try:
            self.delete()
        except Exception as e:
            log.logger.error(str(e.message))
            raise
        log.logger.debug("Teardown of {0} completed.".format(self.file_name))
