#!/usr/bin/env python
#
# ********************************************************************
# Ericsson LMI                 Utility Script
# ********************************************************************
#
# (c) Ericsson LMI 2017 - All rights reserved.
#
# The copyright to the computer program(s) herein is the property of Ericsson LMI. The programs may be used
# And/or copied only with the written permission from Ericsson LMI or in accordance with the terms and conditions stipulated
# In the agreement/contract under which the program(s) have been supplied.
#
# ********************************************************************
# Name    : workload
# Purpose : Tool that provisions a pool of nodes for load testing
# ********************************************************************

"""
workload - Tool that allows users to create load in ENM system
Usage:
  workload start PROFILES [--conf <path>] [--category] [--network-check] [--ignore <profiles>] [--network-config <configuration>] [--schedule <path_to_schedule>]
                          [--force] [--include <supported_types>] [ -r | --release-exclusive-nodes] [--no-exclusive] [--priority=<PRIORITY>] [--updated] [options]
  workload status [PROFILES] [--no-ansi] [--json] [[--errors | --verbose | --lastrun | --warnings] | (--verbose --error-type=<TYPES>) | (--errors --error-type=<TYPES>) | (--errors --warnings)]
                             [--network-check] [-t <total> | --total <total>] [-c | --category] [--priority=<PRIORITY>] [options]
  workload stop PROFILES [--category] [--ignore <profiles>] [--force-stop] [--initial-install-teardown] [--skip] [--schedule <path_to_schedule>]
                         [ -r | --release-exclusive-nodes] [--priority=<PRIORITY>] [--no-ansi] [options]
  workload restart PROFILES [--conf <path>] [--category] [--network-check] [--ignore <profiles>] [--network-config <configuration>] [--force-stop] [--force]
                            [--schedule <path_to_schedule>] [--supported | --updated] [ -r | --release-exclusive-nodes] [--no-exclusive]
                            [--include <supported_types>] [--priority=<PRIORITY>] [options]
  workload reset [--no-ansi] [--network-values]
  workload category [--no-ansi]
  workload profiles [--no-ansi] [--exclusive]
  workload clean-pid PROFILES [--no-ansi]
  workload export PROFILES [--category] [--no-ansi]
  workload describe PROFILES [--no-ansi] [--category]
  workload remove IDENTIFIER [RANGE] [--force] [--no-ansi]
  workload clear-errors [PROFILES] [--category] [--no-ansi]
  workload add IDENTIFIER [RANGE | --profiles <profiles>] [--validate] [--no-ansi]
  workload list IDENTIFIER [--json] [--profiles <profiles>] [--no-ansi] [options]
  workload kill [PROFILES] [--no-ansi]
  workload diff [PROFILES] [--category] [--rpm-version=<VERSION>] [--network-size=<SIZE>] [--no-ansi] [--updated] [--priority=<PRIORITY>] [-l | --list-format] [--nodes] [--node-poids]

Arguments:
   IDENTIFIER     For the 'add', 'remove' and 'list' operations, it is a unique identifier for a specified node or set of nodes to be added to the workload pool
                  (i.e., the identifier specified when node_populator 'parse' operation was run).
                  When using 'list' must be a comma delimited list of node names or unix file patterns for e.g., every node from simulation LTE01: *LTE01*

   RANGE          Performs the operation on a subset of nodes in the specified range

   PROFILES       Name or comma delimited list of workload profiles or categories (when --category option is also specified)
   ALL            Performs the operation on all profiles/nodes.

Options:
  -h, --help                           Shows this screen
  -c, --category                       Start all profiles in a given category
  --conf <path>                        Path to the python file that holds the modified profile configuration
  --csv                                Outputs the status report in csv format
  --errored-nodes                      Deprecated
  --errors                             Displays profiles errors only omitting info and summary
  --warnings                           Display all the profile warnings. Used in combination with: --errors
  --error-type=<TYPE_A>,<TYPE_B>       Displays only errors of the specified type(s). Accepted types [NETSIM, APP, PROFILE]
  --force                              Starts profiles, regardless of its SUPPORTED status
  --force-stop                         Option required to stop or restart foundation type profile
  --include <supported_types>          Supported types to include when starting profiles on top of the profiles marked as supported
  --ignore <profiles>                  Profiles to be ignored
  --initial-install-teardown           Stop profile processes, delete existing profile logs, without cleaning the ENM objects before performing an Initial Installation
  --json                               Converts the output to JSON format
  --lastrun                            Sorts profiles in order of when they were last run descending
  -l, --list-format                    List profiles in a space separated list
  --network-config <configuration>     Start profiles with a defined configuration file. Options include 60k, 40k, 15k, 5k, soem, extra-small, 20k_transport, 10k_transport
  -n, --network-check                  Executes a network health check
  --no-ansi                            Removes ANSI codes responsible for text formatting
  --priority <priority_rating>         Displays profiles with specified priority rating, must be of value 1 or 2
  -p, --profiles <profiles>            List of comma separated profile names
  --schedule <path_to_schedule>        Starts profiles based on a python schedule file. Template schedule file /opt/ericsson/enmutils/etc/schedule_template.py
  -N, --no-sleep                       Prevent last profile from performing specified schedule sleep
  --skip                               Allows the user to skip, confirmation of the quick teardown request
  -v, --verbose                        Displays full workload output
  -s, --supported                      Used with restart to restart all supported workload including non running profiles
  -t <total>, --total <total>          Value of total records to be displayed. Used in combination with: --errors
  -u, --updated                        Show all updated profiles in workload diff
  --validate                           Validate that nodes being added to the pool are synchronized
  -r, --release-exclusive-nodes        Restart the specified profiles, and release EXCLUSIVE profile nodes
  -x, --no-exclusive                   Start the profiles, without allocating nodes to be used by EXCLUSIVE profiles
  --new-only                           Select the new profiles that have been installed eg new profiles in installed rpm 4.43.11, not in the previous rpm 4.43.10
  --version <rpm>                      Specify a specific rpm version to be used: 4.48.10, can be used with --new-only to amend the previous rpm from the default option
  --soak                               REL flag
  --no-network-size-check              Skip the cmedit checks to determine network size
  --test-only                          Update supported profiles with test profile names
  --jenkins                            Identify the caller of the tool as jenkins
  --network-values                     Reset the cell count of the network and the network type
  --message <message>                  Message to be logged as part of operation
  --robustness                         Flag to select the respective robustness configuration
  --exclusive                          Prints the list of exclusive profiles
  --nodes                              Prints the difference nodes between the workload pool and ENM
  --node-poids                         Prints the difference of nodes poid data between the workload pool and ENM

Examples:
  workload start all
    Starts all profiles according the schedule in enmutils_int/lib/schedules/full_schedule.py file
  workload restart all
    Restarts all active/running profiles according to the start schedule in enmutils_int/etc/full_schedule.py
  workload reset
    Resets all nodes in the workload node pool to their default state if no profiles are running on any nodes. If profiles are running it will remove errors only from the nodes
  workload category
    Display all existing categories
  workload profiles
    Display all existing profiles
  workload describe all
    Provides a link to the latest ENM TERE link to source profile description & in addition display current profile values
  workload remove all
    Removes all nodes from the workload node pool if no profiles are running on any nodesi (will not work if there are profiles running on the system)
  workload add pm_test_nodes
    Adds the nodes from the pm_test_nodes file to the workload node pool
  workload list all
    Lists all the properties for all nodes in the workload pool
  workload diff
    Displays profiles info as per installed version of ERICtorutilitiesinternal_CXP9030579 with tabular summary
  workload kill <profile_name>
    Kills a profile when profile stucks in stop/start state - Warning : This command is only for internal use , BR will not own any issues faced if this command is used.
    Please note that this kill command will just kill the profile, it will not perform the teardown actions like deallocation of nodes, remove the attributes, remove the users created.

Notes:
  When using --conf <path>, new config file must hold the new attribute values in a dictionary with the profile name as the dict name e.g: PM_08 = {"NUM_NODES": 10, ...}
  For --network-config, supported values are: 60k, 40k, 15k, 5k, soem, extra-small, 20k_transport, 10k_transport
  For --network-type, supported values are: cpp, ecim, ip
  For reference : https://eteamspace.internal.ericsson.com/display/ERSD/workload
"""
import pkgutil
import re
import sys
import signal
import unipath

from enmutils.lib.exceptions import SessionNotEstablishedException
from enmutils.lib import (log, exception, init, config)
from enmutils_int.lib import load_mgr, workload_ops, workload_ops_node_operations
from enmutils_int.lib.services.profilemanager_helper_methods import get_all_profile_names, get_categories

from docopt import docopt

ENMUTILS_INT_PATH = unipath.Path(pkgutil.get_loader('enmutils_int').filename)
LIB_PATH = ENMUTILS_INT_PATH.child('lib')
WORKLOAD_PATH = LIB_PATH.child('workload')
NETWORK_SIZES = {'5k': 'five_k_network', 'soem_5k': 'five_k_network', '15k': 'fifteen_k_network', '40k': 'forty_k_network', '60k': 'sixty_k_network',
                 'five_k_network': 'five_k_network', 'soem_five_k_network': 'soem_five_k_network', 'fifteen_k_network': 'fifteen_k_network', 'forty_k_network': 'forty_k_network', 'sixty_k_network': 'sixty_k_network',
                 'transport_twenty_k_network': 'transport_twenty_k_network', 'transport_ten_k_network': 'transport_ten_k_network'}


def _validate_profiles(argument_dict):
    """
    Validate supplied profiles.
    :param argument_dict: argument dictionary with user inputs.
    :type argument_dict: dict
    :return: list of valid profiles
    :rtype: list
    :raises RuntimeError: raises if there is no valid profiles or no valid category supplied
    """
    valid_profiles = []

    if argument_dict['status'] and not argument_dict['PROFILES']:
        argument_dict['PROFILES'] = 'all'

    if argument_dict['--new-only']:
        valid_profiles = load_mgr.get_new_profiles(argument_dict['--version'])
    elif argument_dict['start'] and argument_dict['--updated']:
        valid_profiles = load_mgr.get_updated_profiles()
    elif argument_dict['PROFILES']:
        user_supplied = _remove_duplicates(argument_dict['PROFILES'].split(","))

        if argument_dict['--category'] and argument_dict['PROFILES'] != 'all':
            valid_categories, _ = _validate_categories(user_supplied)
            if valid_categories:
                valid_profiles = _get_existing_profiles_in_categories(valid_categories)
            else:
                raise RuntimeError("No valid categories provided. Run 'workload category' to view valid categories")
        elif argument_dict['PROFILES'] == 'all':
            # set explicitly to None, as stop / start / restart/ describe -
            # all will need to deal with it in a different way
            # as 'all' means different things for 'stop' than for start'
            valid_profiles = []
        else:
            valid_profiles, _ = _do_profiles_validation_against_existing_profiles(user_supplied)
            if not valid_profiles:
                raise RuntimeError("No valid profile names provided")

    valid_profiles = sorted(valid_profiles) if valid_profiles else valid_profiles

    return valid_profiles


def _update_config(argument_dict, profile_names):
    """
    Update config based on command line args.
    :param argument_dict: Command line argument dict.
    :type argument_dict: dict
    :param profile_names: List of profile names.
    :type profile_names: list
    :raises RuntimeError: if --network-config argument is not supported.
    """
    valid_network_configurations = ['60K', '40K', '15K', '5K', 'SOEM', 'EXTRA-SMALL', '20K_TRANSPORT', '10K_TRANSPORT']
    non_default_network_configurations = ['SOEM', 'EXTRA-SMALL', '20K_TRANSPORT', '10K_TRANSPORT']
    config.set_prop('DEFAULT_VALUES', True)
    if argument_dict['--new-only'] and profile_names or argument_dict['--soak']:
        config.set_prop('SOAK', True)
    if argument_dict['--no-sleep']:
        config.set_prop('SLEEP', True)
    if argument_dict['--network-config']:
        if str(argument_dict['--network-config']).upper() in valid_network_configurations:
            config.set_prop('network_config', argument_dict['--network-config'])
        else:
            raise RuntimeError('Invalid argument passed for --network-config. '
                               'Supported values: {0}'.format(', '.join(valid_network_configurations)))
        if str(argument_dict['--network-config']).upper() in non_default_network_configurations:
            config.set_prop('DEFAULT_VALUES', False)


def _validate_categories(categories):
    """
    Get valid and invalid categories from provided categories

    :param categories: categories to be validated
    :type categories: set
    :rtype: set, set
    :returns: Valid and invalid categories
    """
    all_categories = get_categories()
    valid_categories = categories.intersection(all_categories)
    not_valid_categories = categories.difference(all_categories)

    if not_valid_categories:
        log.logger.info(log.red_text('Invalid Categories: {0}'.format(', '.join(not_valid_categories))))
    return valid_categories, not_valid_categories


def _get_existing_profiles_in_categories(categories):
    """
    Get valid profiles in supplied categories

    :param categories: categories to query for associated profiles
    :type categories: set
    :rtype: list
    :returns: lists of valid profiles as per supplied categories
    """
    valid_profiles = []

    if categories:
        existing_profiles = set(get_all_profile_names())
        valid_profiles = [profile for category in categories for
                          profile in existing_profiles if
                          profile.split('_')[0] == category or re.split(r'_\d{1,2}', profile)[0] == category]
    return valid_profiles


def _do_profiles_validation_against_existing_profiles(profiles_names):
    """
    Validate supplied profiles_names against existing profile names

    :param profiles_names: Profiles names to be validated
    :type profiles_names: set

    :returns: list of valid an invalid profiles_names
    :rtype: list, list
    """
    existing_profiles = set(get_all_profile_names())
    not_existing_profiles = profiles_names.difference(existing_profiles)

    valid_profiles = profiles_names.intersection(existing_profiles)

    if not_existing_profiles:
        log.logger.info(log.red_text('Invalid profile names: {0}'.format(', '.join(not_existing_profiles))))
    return list(valid_profiles), list(not_existing_profiles)


def _remove_duplicates(list_of_values):
    """
    Removes duplicates from a list of values passed in

    :param list_of_values: a list of values
    :type list_of_values: list
    :return: set, containing a list of values where duplicates have been removed
    :rtype: set
    """

    return set([item.lower() for item in list_of_values])


def _ignoring_profiles(profiles_to_ignore):
    """
    Display ignored profiles to the user.

    :param profiles_to_ignore: a comma delimited string of profile names to be ignored
    :type profiles_to_ignore: str
    :return: None or set of valid profiles
    :rtype:  None or set
    """

    ignored_profiles = set(profile.upper() for profile in _remove_duplicates(profiles_to_ignore.split(",")))
    workload_profiles = set([profile.upper() for profile in get_all_profile_names()])
    valid_ignored_profiles = ignored_profiles.intersection(workload_profiles)

    if valid_ignored_profiles:
        log.logger.info("Ignoring the following profiles: {0}".format(",".join(valid_ignored_profiles)))
        return valid_ignored_profiles
    else:
        log.logger.info(log.red_text("The following are not valid profiles: {0}".format(",".join(ignored_profiles))))


def log_workload_message(argument_dict):
    """
    Log the workload stop/start/restart message supplied

    :param argument_dict: Containing the arguments supplied
    :type argument_dict: dict
    """
    if argument_dict['start']:
        operation = "Starting"
    elif argument_dict['stop']:
        operation = "Stopping"
    else:
        operation = "Restarting"
    profile_stub = ("categories::\t[{0}]".format(argument_dict['PROFILES']) if argument_dict['--category'] else
                    "profiles::\t[{0}]".format(argument_dict['PROFILES']))
    supplied_message = argument_dict['--message'] if argument_dict['--message'] else "No message provided."
    message = "{0} {1}.\tMessage supplied with operation::\t[{2}]".format(operation, profile_stub, supplied_message)
    logger = log.get_workload_ops_logger(__name__)
    logger.info(message)


def perform_cli_pre_checks(argument_dict):
    """
    Perform a series of pre check to enable/disable options, confirm and validate requested operation

    :param argument_dict: Dictionary containing user supplied arguments
    :type argument_dict: dit

    :return: Tuple containing profiles to be ignored and the operation to be executed.
    :rtype: tuple
    """
    if argument_dict['start'] or argument_dict['stop'] or argument_dict['restart']:
        if argument_dict['--robustness']:
            config.set_prop("ROBUSTNESS", 'True')
        log_workload_message(argument_dict)
    if argument_dict['--errored-nodes']:
        log.logger.warn("This option is no longer available.")
        init.exit(0)
    if argument_dict['--priority'] and argument_dict['--priority'] not in ["1", "2"]:
        log.logger.error("Invalid priority rating specified: '{0}'. Priority rating must be 1 or 2.".format(
            argument_dict['--priority']))
        init.exit(0)

    # remove all text formatting
    if argument_dict['--no-ansi']:
        config.set_prop("print_color", 'False')

    operation_type = [option for option in argument_dict if argument_dict[option] is True and
                      not option.startswith('--')][0]
    if not argument_dict['--skip'] and argument_dict['--initial-install-teardown']:
        log.logger.info(log.red_text("This command will halt all workload profiles without attempting to teardown the "
                                     "created ENM objects.\nThis functionality should only be used, when an Initial "
                                     "Installation is scheduled.\nDo you wish to continue? (Yes | No)\n"))
        answer = raw_input()
        if not answer.lower() in ["y", "yes"]:
            init.exit(0)

    ignored_profiles = None
    if argument_dict['--ignore']:
        ignored_profiles = _ignoring_profiles(argument_dict['--ignore'])
    if argument_dict['--test-only']:
        config.set_prop('TEST', True)

    return ignored_profiles, operation_type


def display_workload_operation_info_message(operation_type, argument_dict):
    """
    prints the workload operation info message, if operation_type is status and --json value is False.

    :param operation_type: Type of workload operation.
    :type operation_type: str
    :param argument_dict: Command line argument dict.
    :type argument_dict: dict
    """
    if not ("status" in operation_type and argument_dict["--json"]):
        log.logger.info("Workload operations can take some time. Please be patient...")


def cli():
    """
    Parses the command line arguments passed to the workload.py tool
    :raises SystemExit: raises if exception occurs
    """
    argument_dict = {}
    # Register signal handler
    signal.signal(signal.SIGINT, init.signal_handler)

    # Initialize logging and load our configuration properties
    init.global_init("tool", "int", "workload", sys.argv, execution_timeout=60 * 60 * 16)

    # Process command line arguments
    try:
        argument_dict = docopt(__doc__)
    except SystemExit as e:
        # If there is a message that means we had invalid arguments
        if e.message:
            log.logger.info("\n {0}".format(e.message))
            exception.handle_invalid_argument()
        else:
            # Otherwise it is a call to help text and we are exiting with a SystemExit (rc 0)
            raise

    rc = 0
    result = True
    ignored_profiles, operation_type = perform_cli_pre_checks(argument_dict)
    try:
        profile_names = _validate_profiles(argument_dict)
        _update_config(argument_dict, profile_names)
    except RuntimeError as e:
        exception.process_exception(e.message, print_msg_to_console=True)
        result = False
    else:
        display_workload_operation_info_message(operation_type, argument_dict)
        if operation_type in ["add", "remove", "reset"]:
            operation = workload_ops_node_operations.get_workload_operations(operation_type, argument_dict)
        else:
            operation = workload_ops.get_workload_operations(
                operation_type, argument_dict, profile_names=profile_names, ignored_profiles=ignored_profiles)
        try:
            operation.execute()
        except SessionNotEstablishedException:
            log.logger.error(
                "Unable to get or create user administrator session. Retry commmand execution.\n"
                "If problem continues please try logging in manually and verify ENM system is healthy.\n"
                "If no fault in ENM raise support request.")
            exception.process_exception()
            result = False
        except Exception as e:
            exception.process_exception(str(e), print_msg_to_console=True)
            result = False

    if not result:
        rc = 1
    init.exit(rc)


if __name__ == "__main__":  # pragma: no cover
    cli()
