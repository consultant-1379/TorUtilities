#!/usr/bin/env python
# ********************************************************************
# Ericsson LMI                 Utility Script
# ********************************************************************
#
# (c) Ericsson LMI 2014 - All rights reserved.
#
# The copyright to the computer program(s) herein is the property of Ericsson
# LMI. The programs may be used and/or copied only with the written permission
# from Ericsson LMI or in accordance with the terms and conditions stipulated
# in the agreement/contract under which the program(s) have been supplied.
#
# ********************************************************************
# Name    : network
# Purpose : Tool to administer a full network synchronization and monitor the sync status and info of all nodes
# Team    : Blade Runners
# ********************************************************************

"""
network - Tool to administer a full network synchronization and monitor the sync status and info of all nodes

Usage:
  network sync NODE_REGEX
  network sync-list NODES
  network status [--node [NODE_NAME] | --groups [GROUPS]] [--sl] [--show-nodes] [--show-unsynced] [--shm-cpp]
  network netsync [SYNC_GROUPS]
  network info NODE_NAME
  network netypes [NODE_TYPES]
  network clear

Arguments:
   NODE_NAME        Is the name of a network element
   NODE_TYPES       Is a comma delimited list of valid node types

Options:
   --show-unsynced      Option to get the nodes currently unsynchronised under each group
   --show-nodes         Option to get the nodes in any state under each group
   --shm-cpp            Display only the SHM status for CPP platform nodes
   --node               Option to get sync status details on a specific node
   --groups             Get the sync state of a specific group i.e. CM,PM
   --sl                 Short for security level includes information on the nodes security levels (Not included - ECIM:COM nodes)
    -h                  Print this help text

Examples:
    ./network sync *LTE01*
        Sync all nodes which match the pattern *LTE01*

    ./network sync-list LTE06ERBS00156,LTE06ERBS00155,LTE06ERBS00160
        Sync the list of nodes passed in as an argument

    ./network status
        Counts and prints the CM synchronization status for all nodes on the network

    ./network status --show-nodes
        Counts and prints the CM synchronization status for all nodes on the network,
        and lists the CM state of all nodes

    ./network status --show-unsynced
        Counts and prints the CM synchronization status for all nodes on the network,
        and lists all unsynchronised nodes under CM

    ./network status --groups
        Counts and prints the CM,FM,PM and SHM synchronization status for all nodes on the network

    ./network status --groups --show-nodes
        Counts and prints the CM,FM,PM and SHM synchronization status for all nodes on the network,
        and lists the states of all nodes under each group

    ./network status --groups --show-unsynced
        Counts and prints the CM,FM,PM and SHM synchronization status for all nodes on the network,
        and lists all unsynchronised nodes under each group

    ./network status --groups fm,pm
        Counts and prints the FM and PM synchronization status for all nodes on the network.
        List of status' to print is configurable. ie Cm,Fm,Pm and Shm all valid

    ./network status --groups fm,pm --show-nodes
        Counts and prints the FM and PM synchronization status for all nodes on the network,
        and lists the states of all nodes under the specified groups
        List of status' to print is configurable. ie Cm,Fm,Pm and Shm all valid

    ./network status --groups fm,pm --show-unsynced
        Counts and prints the FM and PM synchronization status for all nodes on the network,
        and lists all unsynchronised nodes under the specified groups
        List of status' to print is configurable. ie Cm,Fm,Pm and Shm all valid

    ./network status --sl
        Counts and prints the CM synchronization status for all nodes on the network.
        The --sl flag provides info on security level of nodes.
        ** ECIM:COM nodes are not yet supported. This may cause a discrepancy between synced node count and security level count. **

    ./network status --sl --show-nodes
        Counts and prints the CM synchronization status for all nodes on the network.
        The --sl flag provides info on security level of nodes. --show-nodes will show each node's security level
        ** ECIM:COM nodes are not yet supported. This may cause a discrepancy between synced node count and security level count. **

    ./network status --node LTE01ERBS00018
        Prints the synchronization status of the given node on the network

    ./network status --groups -shm-cpp
        Filter the SHM status to only display nodes with CPP platform

    ./network netsync
        Synchronizes all nodes on the network (Cm, Fm, Pm)

    ./network netsync cm,pm
        Synchronize all node on the network for the provided groups

    ./network info LTE01ERBS00018
        Returns information about the node, i.e. IP Address, OSS Model Identity, NetworkElement Child MOs

    ./network netypes
        Shows supported NE's for this node

    ./network netypes ERBS
        Shows supported NE's for ERBS nodes

    ./network clear
        Clears the entire network

"""
import re
import sys
import time
import signal
from docopt import docopt

from enmutils_int.lib.delete_network import DeleteNetwork
from enmutils_int.lib.enm_user import get_workload_admin_user
from enmutils_int.lib.enm_ne_type_info import print_supported_node_info
from enmutils.lib import log, init, exception, mutexer, timestamp, enm_node_management, cache
from enmutils.lib.exceptions import ValidationError, ScriptEngineResponseValidationError
from enmutils.lib.enm_node_management import CmManagement, FmManagement, PmManagement

# Have positive case as first arguement in status lists
CM_MANAGEMENT_STATUS = ["SYNCHRONIZED", "PENDING", "TOPOLOGY", "UNSYNCHRONIZED", "ATTRIBUTE", "DELTA", "NOT_SUPPORTED"]
FM_MANAGEMENT_STATUS = ["IN_SERVICE", "IDLE", "HEART_BEAT_FAILURE"]
PM_MANAGEMENT_STATUS = ["true", "false"]
SHM_MANAGEMENT_STATUS = ["SYNCHRONIZED", "UNSYNCHRONIZED"]

PREFERRED_SYNC_STATUS_PER_TYPE = {"pm": "true", "cm": "SYNCHRONIZED", "fm": "IN_SERVICE", "shm": "SYNCHRONIZED"}
DEFAULT_SYNC_GROUPS = ["cm", "fm", "pm"]
COMPLETE_SYNC_GROUPS = ["cm", "fm", "pm", "shm"]

WAIT_INTERVAL = 15
TIMEOUT = 1800

SUPERVISE, UNSUPERVISE = range(2)


def sync_nodes(user, groups=None, node_ids="*", regex=None, operation=SUPERVISE):
    """
    Synchronizes all network nodes on the system

    :param user: User object to execute commands as
    :type user: `enm_user_2.User`
    :param groups: Functional groups to sync
    :type groups: list
    :param node_ids: Id of the nodes to sync
    :type node_ids: list
    :param regex: Regex to sync nodes on
    :type regex: str
    :param operation: Integer used to toggle operations
    :type operation: int

    :raises RuntimeError: raised if invalid group supplied
    :raises e: (ScriptEngineResponseValidationError) raised if the ENM request fails

    :return: Boolean indicating if the operation was successful
    :rtype: bool
    """

    log.logger.info(log.cyan_text("\nInitiating {0} {1} on {2} nodes".format(",".join(groups).upper(), "sync" if operation == SUPERVISE else "unsync",
                                                                             len(node_ids) if node_ids != "*" else "all")))

    result = False
    total_cm_nodes, total_fm_nodes, total_pm_nodes, total_shm_nodes = 0, 0, 0, 0
    total_cm_complete_nodes, total_fm_complete_nodes, total_pm_complete_nodes, total_shm_complete_nodes = 0, 0, 0, 0
    cm_completed = fm_completed = pm_completed = shm_completed = True
    management_objects = []

    # Build Management objects for the groups specified
    for group in groups:
        try:
            management_objects.append(getattr(enm_node_management, "{0}Management".format(group.lower().title()))
                                      (user=user, node_ids=node_ids, regex=regex))
        except AttributeError:
            raise RuntimeError(log.red_text("Please ensure you have passed a valid sync group: cm, fm, pm and shm"))

    # Execute sync command on the objects just created
    try:
        for management_obj in management_objects:
            if operation == SUPERVISE:
                management_obj.supervise()
            elif operation == UNSUPERVISE:
                management_obj.unsupervise()
    except ScriptEngineResponseValidationError as e:
        log.logger.error("Please ensure all nodes provided are on the system.")
        raise e

    start_time = timestamp.get_current_time()
    while float(timestamp.get_elapsed_time(start_time)) < TIMEOUT:

        if "cm" in groups:
            cm_completed, total_cm_complete_nodes, total_cm_nodes = _print_sync_status(user, "cm", CM_MANAGEMENT_STATUS,
                                                                                       node_ids=node_ids, regex=regex,
                                                                                       wait_state=("SYNCHRONIZED" if operation == SUPERVISE else "UNSYNCHRONIZED"))
        if "fm" in groups:
            fm_completed, total_fm_complete_nodes, total_fm_nodes = _print_sync_status(user, "fm", FM_MANAGEMENT_STATUS,
                                                                                       node_ids=node_ids, regex=regex,
                                                                                       wait_state="IN_SERVICE" if operation == SUPERVISE else "IDLE")
        if "pm" in groups:
            pm_completed, total_pm_complete_nodes, total_pm_nodes = _print_sync_status(user, "pm", PM_MANAGEMENT_STATUS,
                                                                                       node_ids=node_ids, regex=regex,
                                                                                       wait_state=("true" if operation == SUPERVISE else "false"))
        if "shm" in groups:
            shm_completed, total_shm_complete_nodes, total_shm_nodes = _print_sync_status(user, "shm", SHM_MANAGEMENT_STATUS,
                                                                                          node_ids=node_ids, regex=regex,
                                                                                          wait_state=("SYNCHRONIZED" if operation == SUPERVISE else "UNSYNCHRONIZED"))

        if all([cm_completed, fm_completed, pm_completed, shm_completed]):
            log.logger.info(log.green_text("All nodes in the network have been successfully {0}synchronised\n"
                                           "".format("un" if operation == UNSUPERVISE else "")))
            result = True
            break
        else:
            log.logger.info("Waiting {0} seconds for remaining nodes to sync..."
                            .format(int(TIMEOUT - float(timestamp.get_elapsed_time(start_time)))))
            time.sleep(WAIT_INTERVAL)

    # Print final results of the synchronise action
    log.logger.info(log.underline_text(log.cyan_text("\nFINAL RESULTS:\n")))
    if "cm" in groups:
        _print_final_status("cm", total_cm_complete_nodes, total_cm_nodes, operation=operation)
    if "fm" in groups:
        _print_final_status("fm", total_fm_complete_nodes, total_fm_nodes, operation=operation)
    if "pm" in groups:
        _print_final_status("pm", total_pm_complete_nodes, total_pm_nodes, operation=operation)
    if "shm" in groups:
        _print_final_status("shm", total_shm_complete_nodes, total_shm_nodes, operation=operation)

    return result


def _print_final_status(sync_type, total_synced_nodes, total_nodes, operation=SUPERVISE):
    """
    Outputs the overall status of the operation

    :param sync_type: Sync operation which has been attempted
    :type sync_type: str
    :param total_synced_nodes: Total nodes which are synchronised
    :type total_synced_nodes: int
    :param total_nodes: Total nodes which are created
    :type total_nodes: int
    :param operation: Integer used to toggle operations
    :type operation: int
    """
    if total_nodes == 0:
        log.logger.info(log.red_text("Nodes returned no status for {0}. Please ensure they have been created on the system.".format(sync_type.upper())))
    elif total_synced_nodes != total_nodes:
        log.logger.info(log.red_text("    {0} {1} failed for {2}/{3} nodes".
                                     format(sync_type.upper(), "sync" if operation == SUPERVISE else "unsync", total_nodes - total_synced_nodes, total_nodes)))
    else:
        log.logger.info(log.green_text("    {0} {1} passed for {2}/{3} nodes".
                                       format(sync_type.upper(), "sync" if operation == SUPERVISE else "unsync", total_synced_nodes, total_nodes)))


def _get_sync_status_and_nodes(user, sync_type, node_ids="*", regex=None):
    """
    Returns the sync status, the nodes which are synced and unsynced

    :param user: User object to execute commands as
    :type user: `enm_user_2.User`
    :param sync_type: String indicating the type of sync required
    :type sync_type: str
    :param node_ids: Id of the nodes to sync
    :type node_ids: list
    :param regex: Regex to sync nodes on
    :type regex: str

    :raises Exception: raised if ENM request has failed
    :return:Tuple containing the status, list of synchronised and unsynchronised nodes
    :rtype: tuple
    """

    synced_nodes_list = []
    unsynced_nodes_list = []
    try:
        sync_status = getattr(enm_node_management, "{0}Management".format(sync_type.lower().title())).\
            get_status(user, node_ids=node_ids, regex=regex)
        for key, value in sync_status.iteritems():
            if value == PREFERRED_SYNC_STATUS_PER_TYPE.get(sync_type):
                synced_nodes_list.append(str(key))
                synced_nodes_list = sorted(synced_nodes_list)
            else:
                unsynced_nodes_list.append(str(key))
                unsynced_nodes_list = sorted(unsynced_nodes_list)
    except Exception as e:
        raise Exception("Failed while trying to get status, Exception: {0}".format(e.message))

    return sync_status, synced_nodes_list, unsynced_nodes_list


def _return_total_nodes_for_states(management_states, sync_status, wait_state, node_ids="*"):
    """
    Returns a dict of counts of sync_states along with a list of nodes which reached state in wait_state

    :param management_states: State value(s) for CM/PM/FM/SHM
    :type management_states: list
    :param sync_status: Dictionary containing the status of nodes created on ENM
    :type sync_status: dict
    :param wait_state: Value to be counted
    :type wait_state: object
    :param node_ids: Id of the nodes to sync
    :type node_ids: list

    :return:Tuple containing the status, list of synchronised and unsynchronised nodes
    :rtype: tuple
    """
    sync_state_count = {}
    for state in management_states:
        sync_state_count[state] = sync_status.values().count(state)

    total_complete_nodes = sync_status.values().count(wait_state)
    total_nodes = len(node_ids) if node_ids != "*" else len(sync_status.keys())

    return sync_state_count, total_complete_nodes, total_nodes


def network_health_check():
    """
    Checks CM,FM,PM and SHM and prints to the console if there are any nodes which failed to reached prefered state.
    """

    user = get_workload_admin_user()
    for sync_type in COMPLETE_SYNC_GROUPS:
        sync_status, _, _ = _get_sync_status_and_nodes(user, sync_type)

        if sync_type in PREFERRED_SYNC_STATUS_PER_TYPE:
            _, total_complete_nodes, total_nodes = _return_total_nodes_for_states(management_states=PREFERRED_SYNC_STATUS_PER_TYPE[sync_type],
                                                                                  sync_status=sync_status,
                                                                                  wait_state=PREFERRED_SYNC_STATUS_PER_TYPE[sync_type])
            if total_complete_nodes < total_nodes:
                log.logger.info(log.yellow_text("NETWORK WARNING : {sync_type} {management_type} {total_complete_nodes}/{total_nodes} {status}".format(sync_type=(sync_type.upper()), total_complete_nodes=total_complete_nodes, management_type="SUPERVISION" if sync_type != "pm" else "ENABLED", total_nodes=total_nodes, status=PREFERRED_SYNC_STATUS_PER_TYPE[sync_type])))


def _print_sync_status(user, sync_type, management_states, wait_state, node_ids="*", **kwargs):
    """
    Prints the sync status for all network nodes on the system

    :param user: User object to execute commands as
    :type user: `enm_user_2.User`
    :param sync_type: String indicating the type of sync required
    :type sync_type: str
    :param management_states: State value(s) for CM/PM/FM/SHM
    :type management_states: list
    :param wait_state: Value to be counted
    :type wait_state: object
    :param node_ids: Id of the nodes to sync
    :type node_ids: list
    :param kwargs: Builtin dict for storing and accessing keyword arguments
    :type kwargs: dict

    :return: Tuple containing bool indicating if the operation completed, list of compeleted nodes, list of total nodes
    :rtype: tuple
    """
    regex = kwargs.pop('regex', None)
    nodes = kwargs.pop('nodes', False)
    unsynced = kwargs.pop('unsynced', False)
    completed = False
    sync_status, synced_nodes_list, unsynced_nodes_list = _get_sync_status_and_nodes(user=user, sync_type=sync_type,
                                                                                     node_ids=node_ids, regex=regex)

    sync_state_count, total_complete_nodes, total_nodes = _return_total_nodes_for_states(management_states, sync_status,
                                                                                         wait_state, node_ids=node_ids)

    if sync_status and total_nodes >= 0:
        if not nodes and not unsynced:
            completed = print_synced_node_status(sync_type, sync_state_count, total_nodes, wait_state)
        else:
            print_sync_unsynced_status(unsynced, sync_type, unsynced_nodes_list, synced_nodes_list)
    else:
        log.logger.error("Unable to retrieve Node sync information.\nPlease ensure the nodes are created on the "
                         "deployment and the underlying ENM is in a healthy state.")

    return completed, total_complete_nodes, total_nodes


def print_synced_node_status(sync_type, sync_state_count, total_nodes, wait_state):
    """
    Print the sync state when synced values are only likely available

    :param sync_type: String indicating the type of sync required
    :type sync_type: str
    :param sync_state_count: Dictionary containing the sync state counts
    :type sync_state_count: dict
    :param total_nodes: Total count of node instances found
    :type total_nodes: int
    :param wait_state: Value to be counted
    :type wait_state: object

    :return: Boolean indicating if the operation completed successfully
    :rtype: bool
    """
    completed = False
    if sync_type.upper() == "PM":
        log.logger.info(log.green_text("  {0} ENABLED".format(sync_type.upper())))
    else:
        log.logger.info(log.green_text("  {0} SUPERVISION".format(sync_type.upper())))
    for status, count in sync_state_count.items():
        log.logger.info(log.cyan_text("    {0: <19}: {1}/{2}".format(status, count, total_nodes)))
        if count == total_nodes and wait_state == status:
            completed = True
    return completed


def print_sync_unsynced_status(unsynced, sync_type, unsynced_nodes_list, synced_nodes_list):
    """
    Print the sync state when synced and unsynced values are likely available

    :param unsynced: Boolean indicating if the required value is unsynced nodes
    :type unsynced: bool
    :param sync_type: String indicating the type of sync required
    :type sync_type: str
    :param unsynced_nodes_list: List of the unsynced nodes discovered
    :type unsynced_nodes_list: list
    :param synced_nodes_list: List of the synced nodes discovered
    :type synced_nodes_list: list
    """
    if sync_type.upper() == "PM":
        log.logger.info(log.green_text("  {0} ENABLED".format(sync_type.upper())))
        if unsynced:
            log.logger.info(log.purple_text("\tDisabled:\n \t{0}\n"
                                            .format([node for node in unsynced_nodes_list])))
        else:
            log.logger.info(log.purple_text("\tEnabled:\n  \t{0}\n"
                                            .format([node for node in synced_nodes_list])))
            log.logger.info(log.purple_text("\tDisabled:\n \t{0}\n"
                                            .format([node for node in unsynced_nodes_list])))
    else:
        log.logger.info(log.green_text("  {0} SUPERVISION".format(sync_type.upper())))
        if unsynced:
            log.logger.info(log.purple_text("\tUnsynchronised:\n \t{0}\n"
                                            .format([node for node in unsynced_nodes_list])))
        else:
            log.logger.info(log.purple_text("\tSynchronised:\n  \t{0}\n"
                                            .format([node for node in synced_nodes_list])))
            log.logger.info(log.purple_text("\tUnsynchronised:\n \t{0}\n"
                                            .format([node for node in unsynced_nodes_list])))


def print_node_info(node_name, user):
    """
    Prints the sync status of a node

    :param node_name: Name of the `enm_node.Node` object
    :type node_name: str
    :param user: User object to execute commands as
    :type user: `enm_user_2.User`

    :raises Exception: raised the operation fails

    :return: Indicating if the operation completed successfully
    :rtype: bool
    """

    get_model_identity = "cmedit get NetworkElement={node}"
    get_ip_address = "cmedit get NetworkElement={node} CppConnectivityInformation.ipAddress"
    get_mos = "cmedit get * NetworkElement.networkElementId=={node},*"

    extract_model_id = r"(?<=ossModelIdentity\s:\s)([^|]*)"
    extract_ip_address = r"(?<=ipAddress\s:\s)([^|]*)"
    extract_mos = r"(?<=:\sNetworkElement={0},)([^,]*)"

    result = False
    model_identity, ip_address, cm_status, fm_status, pm_status = None, None, None, None, None

    try:
        model_identity_response = user.enm_execute(get_model_identity.format(node=node_name))
        model_identity_match = re.search(extract_model_id, "|".join(model_identity_response.get_output()))
        if model_identity_match:
            model_identity = model_identity_match.group(0)

        ip_address_response = user.enm_execute(get_ip_address.format(node=node_name))
        ip_address_match = re.search(extract_ip_address, "|".join(ip_address_response.get_output()))
        if ip_address_match:
            ip_address = ip_address_match.group(0)

        cm_status_response = CmManagement.get_status(user, node_ids=[node_name])
        if cm_status_response:
            cm_status = cm_status_response[node_name]

        fm_status_response = FmManagement.get_status(user, node_ids=[node_name])
        if fm_status_response:
            fm_status = fm_status_response[node_name]

        pm_status_response = PmManagement.get_status(user, node_ids=[node_name])
        if pm_status_response:
            pm_status = pm_status_response[node_name]
        mo_list = []
        if not any('0 instance(s)' in value for value in model_identity_response.get_output()):
            node_mos = user.enm_execute(get_mos.format(node=node_name))

            for mo in ",".join(node_mos.get_output()).split("FDN"):
                match = re.search(extract_mos.format(node_name), mo)
                if match and ":" not in match.group(0):
                    mo_list.append(match.group(0))

        node_info = {"ip_address": ip_address or "No data", "model_identity": model_identity or "No data",
                     "cm_status": cm_status or "No data", "fm_status": fm_status or "No data",
                     "pm_status": pm_status or "No data", "mos": ", ".join(mo_list) or "No data"}

        if len(set(node_info.values())) == 1:
            log.logger.warn("\n    Node %s does not exist on the system\n" % node_name)
        else:
            log.logger.info(log.cyan_text("\n      Node: %s " % node_name))
            log.logger.info("\tIP Address                 : %s" % node_info["ip_address"])
            log.logger.info("\tOSS Model Identity         : %s" % node_info["model_identity"])
            log.logger.info("\tCM Supervision             : %s" % node_info["cm_status"])
            log.logger.info("\tFM Supervision             : %s" % node_info["fm_status"])
            log.logger.info("\tPM Subscriptions           : %s" % node_info["pm_status"])
            log.logger.info("\tCreated Network Element MOs: %s\n" % node_info["mos"])
        result = True
    except Exception as e:
        log.logger.error("Could not get all information for node {0}. Exception: {1}".format(node_name, str(e)))

    return result


def print_network_sync_status(user, status=None, nodes=False, unsynced=False):
    """
    Prints the sync status of a network

    :param user: User object to execute commands as
    :type user: `enm_user_2.User`
    :param status: List of status(s) to query, CM/PM/FM/SHM
    :type status: list
    :param nodes: Boolean indicating if unsychronised status should also be displayed
    :type nodes: bool
    :param unsynced: Boolean indicating if the required value is u
    :type unsynced: bool

    :return: Indicating if the operation completed successfully
    :rtype: bool
    """
    result = False
    status = status or ["cm"]

    try:
        invalid_groups = [s for s in status if s not in COMPLETE_SYNC_GROUPS]
        if invalid_groups:
            log.logger.error("Invalid group arguments: {0}".format(",".join(invalid_groups)))

        if "cm" in status:
            _print_sync_status(user, "cm", CM_MANAGEMENT_STATUS, "SYNCHRONIZED", nodes=nodes, unsynced=unsynced)
        if "fm" in status:
            _print_sync_status(user, "fm", FM_MANAGEMENT_STATUS, "IN_SERVICE", nodes=nodes, unsynced=unsynced)
        if "pm" in status:
            _print_sync_status(user, "pm", PM_MANAGEMENT_STATUS, "true", nodes=nodes, unsynced=unsynced)
        if "shm" in status:
            _print_sync_status(user, "shm", SHM_MANAGEMENT_STATUS, "SYNCHRONIZED", nodes=nodes, unsynced=unsynced)
        result = True
    except Exception as e:
        log.logger.error("Unable to retrieve the network sync status, error encountered: [{0}].".format(str(e)))

    return result


def print_node_sync_status(node_name, user):
    """
    Prints the sync status of a node

    :param node_name: Name of the `enm_node.Node` object
    :type node_name: str
    :param user: User object to execute commands as
    :type user: `enm_user_2.User`

    :return: Indicating if the operation completed successfully
    :rtype: bool
    """

    result = False

    try:
        log.logger.info("\n    Node:\t%s\n" % log.green_text(node_name))
        for sync_type in COMPLETE_SYNC_GROUPS:
            status = getattr(enm_node_management, "{0}Management".format(sync_type.lower().title())).get_status(user, node_ids=[node_name]).values()[0].strip()
            log.logger.info("    %s Status:\t%s\n" % (sync_type.upper(), log.cyan_text(status)))
        result = True
    except:
        log.logger.error("Could not get sync state for node {0}".format(node_name))

    return result


def clear_network(user):
    """
    Unsyncs and deletes all NetworkElements, MeContexts and SubNetworks on ENM

    :type user: enm_user_2.User
    :param user: User to use for deleting network through script engine

    :return: Boolean indicating the operation was successful
    :rtype: bool
    """
    try:
        sync_success = sync_nodes(user, groups=COMPLETE_SYNC_GROUPS, operation=UNSUPERVISE)
    except ScriptEngineResponseValidationError as e:
        log.logger.error("Failed to perform unsync operation on nodes. Response was {0}"
                         "".format("\n".join(line for line in e.response.get_output() if line)))
        sync_success = False
    delete_success = _delete_network(user)
    return all([sync_success, delete_success])


def _delete_network(user):
    """
    Deletes all NetworkElements, MeContexts and SubNetworks on ENM

    :type user: enm_user_2.User
    :param user: User to use for deleting network through script engine

    :return: Boolean indicating the operation was successful
    :rtype: bool
    """
    log.logger.info(log.underline_text(log.cyan_text("\nNETWORK DELETION:\n")))
    result1 = _delete_network_mo("deleteNrmDataFromEnm", user)
    result2 = _delete_network_mo("NetworkElement", user)
    result3 = _delete_network_mo("SubNetwork", user)
    return all([result1, result2, result3])


def _delete_network_mo(network_mo, user):
    """
    Deletes all of a specified Network MO on ENM

    :type network_mo: string
    :param network_mo: Network MO to dleete
    :type user: enm_user_2.User
    :param user: User to use for deleting network MO through script engine

    :raises RuntimeError: raised if delete operation fails

    :return: Indicating if the operation completed successfully
    :rtype: bool
    """
    delete_network_obj = DeleteNetwork(user=user)
    result = True
    if network_mo == "deleteNrmDataFromEnm":
        delete_func = delete_network_obj.delete_nrm_data_from_enm
    elif network_mo == "NetworkElement":
        delete_func = delete_network_obj.delete_network_element
    elif network_mo == "MeContext":
        delete_func = delete_network_obj.delete_mecontext
    elif network_mo == "SubNetwork":
        delete_func = delete_network_obj.delete_nested_subnetwork
    else:
        raise RuntimeError(
            "Please specify either deleteNrmDataFromEnm, NetworkElement, MeContext or SubNetwork as network mo")

    try:
        delete_func()
        log.logger.info(
            log.green_text("    " + "[SUCCESS]") + " Delete {0}".format(network_mo))
    except ScriptEngineResponseValidationError as e:
        result = False
        log.logger.error("    [FAIL] Delete {0} failed".format(network_mo))
        log.logger.info("    Command: {0}".format(e.response.command))
        log.logger.info("    Response: {0}".format("\n    ".join([line for line in e.response.get_output() if line])))

    return result


def print_security_levels(user, show_nodes=False):
    """
    Prints the current security level of the created nodes on ENM, SL1/SL2/SL3

    :param user: User object to execute commands as
    :type user: `enm_user_2.User`
    :param show_nodes: Boolean indicating if the node information should also be displayed
    :type show_nodes: bool

    :raises RuntimeError: raised if the ENM request has failed.
    """
    NAME = "Security Level {}"
    EXTRACT_LEVEL = r"(?<=level\s)(\d+)"

    response = user.enm_execute("secadm sl get *")
    output = response.get_output()

    if not any("Command Executed Successfully" in line for line in output):
        raise RuntimeError("Failed to execute get security level command for all nodes.")

    log.logger.info(log.green_text("  NODE SECURITY LEVELS"))

    level_count = {NAME.format(i + 1): 0 for i in xrange(3)}

    for security_info in output:
        level = re.search(EXTRACT_LEVEL, security_info)

        if level:
            level_count[NAME.format(level.group(0))] += 1

    for level, count in level_count.iteritems():
        log.logger.info(log.cyan_text("    {0}   : {1}".format(level, count)))

    if show_nodes:
        log.logger.info(log.green_text("  NODE SECURITY LEVEL MAPPING:"))
        for entry in output[1:len(output) - 1]:
            log.logger.info(log.cyan_text("    {0}".format(entry)))


def cli():

    # Register signal handler
    signal.signal(signal.SIGINT, init.signal_handler)

    # Initialize logging and load our configuration properties
    tool_name = "network"
    init.global_init("tool", "int", tool_name, sys.argv, execution_timeout=2000)

    # Process command line arguments
    try:
        arguments = docopt(__doc__)
    except SystemExit as e:
        # If there is a message that means we had invalid arguments
        if e.message:
            log.logger.info("\n {0}".format(e.message))
            exception.handle_invalid_argument()
        # Otherwise it is a call to help text
        else:
            raise

    try:
        user = get_workload_admin_user()
    except RuntimeError as e:
        exception.process_exception(e.message, True, True)
    success = False

    rc = 1
    nodes = None
    unsynced = None
    try:
        with mutexer.mutex("network-execute-network-command", persisted=True):
            # Retest when set command is confirmed working
            if arguments["sync"]:
                success = sync_nodes(user, groups=DEFAULT_SYNC_GROUPS, regex=arguments['NODE_REGEX'])
            elif arguments["sync-list"]:
                sync_nodes(user, groups=DEFAULT_SYNC_GROUPS, node_ids=arguments['NODES'].split(","))
            elif arguments["netsync"]:
                if arguments["SYNC_GROUPS"]:
                    success = sync_nodes(user, [action.lower() for action in arguments['SYNC_GROUPS'].split(",")])
                else:
                    success = sync_nodes(user, groups=DEFAULT_SYNC_GROUPS)
            elif arguments["status"]:
                if arguments["--shm-cpp"]:
                    cache.set("SHM_CPP", True)
                if arguments["--show-nodes"] or arguments["--show-unsynced"]:
                    if arguments["--node"]:
                        raise ValidationError("[--node] is an invalid argument for actions "
                                              "[--show-nodes | --show-unsynced].")
                if arguments["--show-nodes"]:
                    nodes = True
                if arguments["--show-unsynced"]:
                    unsynced = True
                if arguments["--node"]:
                    if arguments["NODE_NAME"]:
                        success = print_node_sync_status(arguments["NODE_NAME"], user)
                    else:
                        raise RuntimeError(log.red_text("Please ensure you have passed in a node name after --node. "
                                                        "e.g. network status --node netsim_LTE03ERBS00139"))
                elif arguments["--groups"]:
                    if arguments["GROUPS"]:
                        success = print_network_sync_status(user, [action.lower() for action in arguments["GROUPS"].split(",")],
                                                            nodes=nodes, unsynced=unsynced)
                    else:
                        success = print_network_sync_status(user, COMPLETE_SYNC_GROUPS, nodes=nodes, unsynced=unsynced)
                else:
                    success = print_network_sync_status(user, nodes=nodes, unsynced=unsynced)
                if arguments["--sl"]:
                    print_security_levels(user, show_nodes=arguments["--show-nodes"])
            elif arguments["info"]:
                success = print_node_info(arguments["NODE_NAME"], user)
            elif arguments["netypes"]:
                models = arguments["NODE_TYPES"].split(",") if arguments["NODE_TYPES"] else None
                print_supported_node_info(user, models)
                success = True
            elif arguments["clear"]:
                success = clear_network(user)

        if success:
            rc = 0
    except:
        exception.handle_exception(tool_name)

    init.exit(rc)


if __name__ == '__main__':
    cli()
