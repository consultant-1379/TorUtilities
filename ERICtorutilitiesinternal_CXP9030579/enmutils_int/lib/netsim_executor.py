# ********************************************************************
# Name    : NetSim Executor
# Summary : Functional module for interacting with NetSim hosts.
#           Allows the user to deploy executor script, run commands
#           on the Netsim host, run commands on supplied Network
#           Element(s), check the started state of nodes, parse the
#           response.
# ********************************************************************

import os
import pkgutil
import re

from unipath import Path

from enmutils.lib import persistence, shell, cache, filesystem, mutexer, log
from enmutils.lib.exceptions import NetsimError
from enmutils_int.lib.simple_sftp_client import upload

ENMUTILS_INT_PATH = Path(pkgutil.get_loader('enmutils_int').filename)


def run_ne_cmd(cmd, host, sim, node_names, password=None, keep_connection_open=True):
    """
    Runs a command on a given list of nodes in a specified simulation on a specified Netsim box

    :param cmd: The command to be run on Netsim
    :type cmd: str
    :param host: The Netsim box you want to access
    :type host: str
    :param sim: The simulation you wish to use on the Netsim box
    :type sim: str
    :param node_names: A list of node_names you wish to use
    :type node_names: list
    :param password: The password to the netsim host
    :type password: str
    :param keep_connection_open: Boolean indicating if the connection to the NetSim host should be kept alive
    :type keep_connection_open: bool

    :returns: response of the command executed on the nodes
    :rtype: dict
    """
    response = run_cmd(cmd, host, sim, node_names, password, keep_connection_open=keep_connection_open)
    response_dict = _parse_ne_response(response, node_names)
    if "all" in response_dict:
        if "OK" in response_dict["all"]:
            response_dict = {node: 'OK' for node in node_names}
        else:
            response_dict = {node: 'FAIL' for node in node_names}
    return response_dict


def _parse_ne_response(response, node_names):
    """
    Parses the response after running the command on a specific set of nodes in a simulation remotely and returns a dict

    :param response: Response object retrieved from running the remote ne command
    :type response: shell.response object
    :param node_names: A list of node names to run the command on
    :type node_names: list

    :returns: response whether OK or FAIL for given nodes
    :rtype: dict
    """

    nodes = {}
    if response.ok:
        response_desc = _prepare_response(response, node_names)
        match_enable_disable_status = re.findall('enabled|disabled', response_desc)
        match_operationsucceeded = re.findall('OperationSucceeded', response_desc)
        match_ok = re.findall('OK', response_desc, re.IGNORECASE)
        match_exec = re.findall('EXECUTED', response_desc)
        match_true = re.findall('true', response_desc)
        match_child = re.findall('do not create gerancell child', response_desc)
        node_found = any(node_name in response_desc for node_name in node_names)
        if node_found:
            for node_name in node_names:
                if node_name in response_desc:
                    node_status = _check_response_for_node_result(node_name, response_desc)
                else:
                    node_status = 'OK'

                nodes[node_name] = node_status
        elif any([_ for _ in [match_ok, match_exec, match_operationsucceeded, match_true, match_enable_disable_status,
                              match_child] if len(_) == 1]):
            nodes["all"] = 'OK'
        else:
            nodes['all'] = 'FAIL'

    else:
        nodes['all'] = 'FAIL'

    return nodes


def _check_response_for_node_result(node_name, response_desc):
    """
    Checks a string for a particular node name to see if 'OK' is specified after the name

    :param node_name: The name of the node to check for in the string
    :type node_name: string
    :param response_desc: The string to search for the node name and determine the result of the operation for.
    :type response_desc: dict

    :return: 'OK' if OK was found beside the node name or 'FAIL' otherwise
    :rtype: string
    """
    end_index = response_desc.index(node_name) + len(node_name)
    node_result = response_desc[end_index: end_index + 6]
    if 'OK' in node_result or 'EXEC' in node_result or 'ACCEPTED' in node_result:
        node_status = 'OK'
    else:
        ok_line = [line for line in response_desc.split('\n') if line == 'OK']
        node_status = 'FAIL'
        if len(ok_line) > 0:
            node_status = 'OK'
    return node_status


def _prepare_response(response, node_names=None):
    """
    Strips down the response to remove node names from the command in the response and 'Id's from the response text

    :type response: shell.response object
    :param response: Response object retrieved from running the remote command
    :type node_names: list
    :param node_names: A list of node names the command was run against
    :rtype: string
    :returns: A formatted response
    """

    cmd_in_resp = ""
    if node_names:
        cmd_in_resp = response.stdout.split("\n")[0]
        for node_name in node_names:
            cmd_in_resp = re.sub(r'{}'.format(node_name), '___', cmd_in_resp)

        # put it all back together
        cmd_in_resp = "{}\n".format(cmd_in_resp)
        response_str = "{}{}".format(cmd_in_resp, "\n".join(response.stdout.split("\n")[1:]))
    else:
        response_str = response.stdout

    formatted_response = re.sub(r'Id:\s\d+\n', '', response_str)

    return formatted_response


def run_cmd(cmd, host, sim=None, node_names=None, password='netsim', executor_script_path="/tmp/command_executor.sh",
            **kwargs):
    # This function should be merged with shell.run_remote_cmd or altered to state this function is only for running
    # towards netsims as the password is hardcoded and the below call to shell hardcode's the user also as netsim.
    # Make amendments as part of JIRA TORF-242378. Run_sim_cmd and run_ne_cmd need to be looked at during this change
    # along with removing calls to this function overiding the password to None to avoid the below password check
    """
    Runs a command on a given host.
    :param cmd: The command to be run
    :type cmd: str
    :param host: The host the command is to be run on
    :type host: str
    :param sim: The simulation you wish to use on the Netsim box
    :type sim: str
    :param node_names: A list of node_names you wish to use
    :type node_names: list
    :param password: The password to the netsim host
    :type password: str
    :param executor_script_path: str, path to the remote command_executor
    :type executor_script_path: str
    :param kwargs: Dictionary __builtin__ containing optional arguments
    :type kwargs: dict

    :returns: shell.Response instance after executing the command on the given host, sim and nodes
    :rtype: shell.Response
    """
    log_cmd = kwargs.pop('log_cmd', True)
    keep_connection_open = kwargs.pop('keep_connection_open', True)
    node_names = node_names or []

    if not password:
        password = 'netsim'

    key = "command-executor-is-on-netsim-host-{0}".format(host)

    if not cache.has_key(key):
        with mutexer.mutex("check-for-command-executor-on-host-{0}".format(host), persisted=True):
            if persistence.has_key(key):
                log.logger.debug("The key: '{0}' is already set in persistence by another profile so we are setting it "
                                 "in the cache here for this separate process as we don't need to redeploy the script"
                                 .format(key))
                cache.set(key, True)
            else:
                local_path = os.path.join(ENMUTILS_INT_PATH, "external_sources", "scripts", "command_executor.sh")
                deploy_script(host, local_path=local_path, remote_path=executor_script_path)
                log.logger.debug("The netsim executer script on host: '{0}' in location: '{1}' has been deployed "
                                 "successfully".format(host, executor_script_path))
                cache.set(key, True)
                persistence.set(key, True, 900)

    # Build up the command to be executed
    netsim_cmd = "{0} '{1}'".format(executor_script_path, cmd)

    if sim:
        netsim_cmd = "{0} '{1}'".format(netsim_cmd, sim)

        if node_names:
            if isinstance(node_names, list):
                node_names = " ".join(node_names)
            netsim_cmd = "{0} '{1}'".format(netsim_cmd, node_names)

    response = shell.run_remote_cmd(shell.Command(netsim_cmd, timeout=600, allow_retries=False, log_cmd=log_cmd), host,
                                    "netsim", password, add_linux_timeout=True,
                                    keep_connection_open=keep_connection_open)

    return response


def deploy_script(host, local_path, remote_path, permissions=755, user='netsim', password='netsim', force=False):
    """
    Ensures that the script is located on the netsim, if not it will upload it. Optionally changes permissions of file

    :type host: string
    :param host: hostname of netsim target
    :type local_path: string
    :param local_path: path to local file
    :type remote_path: string
    :param remote_path: path to remote location
    :param permissions: file permissions for the script
    :type permissions: int
    :param user: user for the netsim host
    :type user: str
    :param password: password for the netsim host
    :type password: str
    :param force: boolean value if deploy script is to be forced
    :type force: bool

    :raises RuntimeError: if the script is not available on netsim host or unable to set permissions to the deployed
                          script on netsim host
    """

    if (force or not filesystem.does_remote_file_exist(remote_path, host, user, password) or
            filesystem.get_local_file_checksum(local_path) != filesystem.get_remote_file_checksum(
                remote_path, host, user, password)):

        try:
            upload(host, user, password, remote_path, local_path, file_permissions=permissions)
        except IOError as e:
            raise RuntimeError(str(e))


def check_nodes_started(nodes):
    """
    Runs the show started command and checks for the IP in the response
    :type nodes: list
    :param nodes: List of nodes to check status of
    :raises NetsimError: if fails to connect to the netsim host
    :rtype: list
    :return: list of nodes which are stopped
    """
    checked_nodes = []
    found_nodes = []
    nodes_dict = {}

    for host in set(node.netsim for node in nodes):
        nodes_dict[host] = [node for node in nodes if node.netsim == host]

    for host, node_list in nodes_dict.items():
        try:
            checked_nodes.extend(node_list)
            response = run_cmd(".show started", host)
            for node in node_list:
                match = re.search(r"\D{0}\D".format(node.node_ip), response.stdout)
                if match:
                    found_nodes.append(node)
        except Exception as e:
            raise NetsimError("Failed to connect to netsim {0}: {1}".format(host, e.message))
    return set(checked_nodes) - set(found_nodes)
