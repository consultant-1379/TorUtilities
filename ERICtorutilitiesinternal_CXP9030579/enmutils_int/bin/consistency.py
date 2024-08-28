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
# Name    : consistency
# Purpose : Tool to administer the consistency of the node pool
# Team    : Blade Runners
# ********************************************************************

"""
consistency - Tool to administer the consistency of the node pool

Usage:
  consistency check [-e | --enm] [-s | --show-nodes]
  consistency resolve [-d | --delete-from-enm]
  consistency display [NODE_TYPES] [-s | --show-nodes]

Arguments:
   NODE_TYPES        Type of network element to try ring-fence for usage

Options:
   -e, --enm                            Option compare ENM nodes against the workload
   -s, --show-nodes                     Displays the list of nodes to the end user

Examples:
    ./consistency check
        Check the current pool against the list of ENM nodes

    ./consistency check --enm
        Check the current enm against the list of nodes available in the pool

    ./consistency check --enm --show-nodes
        Check the current enm against the list of nodes available in the pool, show the list of nodes

    ./consistency resolve
        No longer supported, missing nodes should be resolved through use of node_populator, workload add or ENM

    ./consistency display
        Display the total number, of all, of the currently available nodes in the workload pool

    ./consistency display ERBS,MGW
        Display the total number, of ERBS and MGW, of the currently available nodes in the workload pool

    ./consistency display ERBS --show-nodes
        Display the total number and list of nodes, of all, of the currently available nodes in the workload pool

"""
import signal
import sys

from docopt import docopt

from enmutils.lib import log, init, exception
from enmutils_int.lib.consistency_checker import ConsistencyChecker

missing_nodes_on_enm = []
missing_workload_pool_nodes = []


def _validate_arguments(arguments):
    """
    Validates the arguments supplied

    :param arguments: Dictionary of args passed to the tool
    :type arguments: dict
    :return: List of node primary types
    :rtype: list
    """

    node_types = arguments['NODE_TYPES'].split(',') if arguments['NODE_TYPES'] else None
    return node_types


def _show_nodes(nodes):
    """
    Display the list of given nodes to the user

    :type nodes: list
    :param nodes: List of `enm_node.Node` instances
    """
    if isinstance(nodes, set):
        log.logger.info("['{0}']".format("', '".join([node for node in nodes if node])))
    elif getattr(nodes[0], "node_id", False):
        log.logger.info("['{0}']".format("', '".join([node.node_id for node in nodes if node])))
    else:
        log.logger.info("Could not determine node ids.")


def _print_pool_consistency_results(enm=None, show_nodes=False):
    """
    Prints out the results of the pool consistency check

    :param enm: Boolean indicating if ENM should be compared to the pool
    :type enm: bool
    :param show_nodes: Boolean indicating if the list of nodes should be displayed
    :type show_nodes: bool
    """
    checker = ConsistencyChecker()
    if not enm:
        results = checker.pool_is_consistent_with_enm()
        global missing_nodes_on_enm
        missing_nodes_on_enm = results
        msg = "The following nodes do not exist in ENM but are in the workload pool:\nNumber: {0}"
    else:
        results = checker.enm_is_consistent_with_pool()
        global missing_workload_pool_nodes
        missing_workload_pool_nodes = results
        msg = "The following nodes do not exist in the workload pool but are available on ENM:\nNumber: {0}"
    if not len(results):
        log.logger.info("Pool consistency check passed, no missing nodes on deployment.")
    else:
        log.logger.info(msg.format(len(results)))
        if show_nodes:
            _show_nodes(results)


def _retrieve_available_nodes(node_types=None):
    """
    Query the workload pool for the available number of nodes (per node type if required)

    :type node_types: list
    :param node_types: List of node primary types, in str format

    :rtype: list
    :return: List of `enm_node.Node` instances
    """
    available_nodes = []
    checker = ConsistencyChecker()
    if node_types:
        for netype in node_types:
            nodes = checker.get_all_unused_nodes(netype=netype)
            if not nodes:
                log.logger.warn("No available {0} nodes found.".format(netype))
            available_nodes.extend(nodes)
        return available_nodes
    else:
        return checker.get_all_unused_nodes()


def _display_available_nodes(nodes, show_nodes=False):
    """
    Display the available number of nodes (per node type if required)

    :param nodes: List of `enm_node.Node` instances
    :type nodes: list
    :param show_nodes: Boolean indicating if the list of nodes should be displayed.
    :type show_nodes: bool
    """
    if nodes:
        log.logger.info("\nTotal available nodes: {0}".format(len(nodes)))
        groups = {node.primary_type: [node for node in nodes] for node in nodes}
        for key, value in groups.iteritems():
            log.logger.info("Total available {0} nodes: {1}".format(key, len(value)))
            if show_nodes:
                _show_nodes(value)
    else:
        log.logger.info("No available nodes discovered.")


def cli():

    # Register signal handler
    signal.signal(signal.SIGINT, init.signal_handler)

    # Initialize logging and load our configuration properties
    tool_name = "consistency"
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

    rc = 1
    try:
        node_types = _validate_arguments(arguments)

        if arguments['check'] or arguments['resolve']:
            _print_pool_consistency_results(enm=arguments['--enm'] or arguments['--delete-from-enm'],
                                            show_nodes=arguments['--show-nodes'])
            rc = 0
            if arguments['resolve']:
                log.logger.info("\nOption no longer supported, please use alternative methods to resolve "
                                "inconsistencies between ENM and the workload pool.")
        elif arguments['display']:
            _display_available_nodes(_retrieve_available_nodes(node_types=node_types),
                                     show_nodes=arguments['--show-nodes'])
            rc = 0
    except Exception as e:
        exception.handle_exception(tool_name, msg=e.message)

    init.exit(rc)


if __name__ == '__main__':
    cli()
