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
# Name    : utilities
# Purpose : Tool to perform various TorUtilities actions
# Team    : Blade Runners
# ********************************************************************

"""
utilities - Tool to perform various TorUtilities actions

Usage:
    utilities monitor_redis
    utilities remove_workload_admin_session_key
    utilities ddc_plugin_create_increment_files
    utilities improve_command_history_logs

Arguments:

Options:

Examples:
    ./utilities monitor_redis
        Run redis-cli commands (e.g. with options "big-keys", "INFO" etc) to extract certain monitoring info from
        Redis DB. Info will be stored to a file under /var/log/enmutils/redis
    ./utilities remove_workload_admin_session_key
        Removes the session key (from persistence) for the workload_admin user
    ./utilities ddc_plugin_create_increment_files
        Creates increment files for DDC Plugin
    ./utilities improve_command_history_logs
        Improves the history of commands

"""
import signal
import sys

from docopt import docopt
from enmutils.lib import log, init, exception, shell, persistence, mutexer
from enmutils.lib.enm_user_2 import WORKLOAD_ADMIN_SESSION_KEY
from enmutils_int.bin.utilities_helper_methods import append_history_of_commands
from enmutils_int.lib.configure_wlvm_ddc_plugin import create_workload_log_file_increments

TORUTILS_HOME_DIR = "/var/log/enmutils"
REDIS_STATS_LOG_DIR = "{0}/redis".format(TORUTILS_HOME_DIR)
REDIS_STATS_LOG_FILE = "{0}/redis_monitoring.log".format(REDIS_STATS_LOG_DIR)
REDIS_CLI = "/opt/ericsson/enmutils/.env/lib/python2.7/site-packages/enmutils/external_sources/db/redis-cli"
REDIS_PORT = 6379


def remove_workload_admin_session_key():
    """
    Remove the workload_admin_session key as part of RPM install

    :return: Boolean to indicate success or not
    :rtype: bool
    """

    with mutexer.mutex("{0}-session-key".format(WORKLOAD_ADMIN_SESSION_KEY), persisted=True, log_output=True):
        if persistence.get(WORKLOAD_ADMIN_SESSION_KEY):
            log.logger.debug("Removing workload_admin session key")
            persistence.remove(WORKLOAD_ADMIN_SESSION_KEY)

    return True


def monitor_redis():
    """
    Execute all commands in relation to Redis DB monitoring

    :return: Boolean to indicate success or not
    :rtype: bool
    """
    log.logger.debug("Performing actions to monitor Redis DB")
    shell.run_local_cmd(shell.Command("mkdir -p {0}".format(REDIS_STATS_LOG_DIR)))

    if not get_redis_big_keys() or not get_redis_info():
        log.logger.error("Problems encountered running monitor commands - "
                         "see {0}/debug.log for more details".format(TORUTILS_HOME_DIR))
        return

    return True


def insert_timestamp_and_label_in_file(label):
    """
    Insert Timestamp and label into Redis log

    :param label: Label that indicates the type of data in the section that follows
    :type label: str
    """

    command = 'echo "### $(date +%y%m%d.%H%M%S) - {label}: ###"'.format(label=label)
    shell.run_local_cmd(shell.Command("{command} >> {redis_log_file}"
                                      .format(command=command, redis_log_file=REDIS_STATS_LOG_FILE)))


def get_redis_big_keys():
    """
    Get Biggest Keys information from Redis DB

    :return: Boolean to indicate success or failure of command
    :rtype: bool
    """
    log.logger.debug("Getting Biggest Keys in Redis DB")
    insert_timestamp_and_label_in_file("BIGKEYS")

    process_output = "grep 'Biggest string found so far' | awk '{print $7, $9, $10}' | sort -nrk 2 | column -t"
    command = ("{redis_cli} -p {redis_port} --bigkeys | {process_output}"
               .format(redis_cli=REDIS_CLI, redis_port=REDIS_PORT, process_output=process_output))

    response = shell.run_local_cmd(shell.Command("{command} >> {redis_log_file}"
                                                 .format(command=command, redis_log_file=REDIS_STATS_LOG_FILE)))

    return True if not response.rc else False


def get_redis_info():
    """
    Get Redis DB statistics using INFO option

    :return: Boolean to indicate success or failure of command
    :rtype: bool
    """
    log.logger.debug("Getting Redis DB stats")
    insert_timestamp_and_label_in_file("INFO")

    process_output = "egrep -i 'used_memory_human|used_memory_peak_human|mem_fragmentation_ratio|connected_clients|" \
                     "redis_version|tcp_port|instantaneous_ops_per_sec|db0'"
    command = ("{redis_cli} -p {redis_port} INFO | {process_output}"
               .format(redis_cli=REDIS_CLI, redis_port=REDIS_PORT, process_output=process_output))

    response = shell.run_local_cmd(shell.Command("{command} >> {redis_log_file}"
                                                 .format(command=command, redis_log_file=REDIS_STATS_LOG_FILE)))

    return True if not response.rc else False


def ddc_plugin_create_increment_files():
    """
    Execute DDC plugin Delta operations

    :return: Boolean to indicate success or not
    :rtype: bool
    """
    return create_workload_log_file_increments()


def improve_command_history_logs():
    """
    Updates and improves the history of commands
    """
    append_history_of_commands()


def cli():
    """
    Main control function that is executed when the script is run

    """
    # Register signal handler
    signal.signal(signal.SIGINT, init.signal_handler)

    # Initialize logging and load configuration properties
    tool_name = __file__.split('.')[0]
    init.global_init("tool", "int", tool_name, sys.argv, execution_timeout=2000)

    command_dict = {}
    # Process command line arguments
    try:
        command_dict = docopt(__doc__)
    except SystemExit as e:
        if e.message:
            log.logger.info("{0}".format(e))
            exception.handle_invalid_argument()
        else:
            raise

    rc = 1
    try:
        utilities_function_name = [command for command in command_dict.keys() if command_dict[command]][0]
        rc = 0 if globals()[utilities_function_name]() else 1
    except Exception as e:
        exception.handle_exception(tool_name, msg=str(e))

    init.exit(rc)


if __name__ == '__main__':  # pragma: no cover
    cli()
