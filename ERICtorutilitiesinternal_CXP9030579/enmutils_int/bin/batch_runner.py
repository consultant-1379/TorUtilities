#!/usr/bin/env python
# ********************************************************************
# Ericsson LMI                 Utility Script
# ********************************************************************
#
# (c) Ericsson LMI 2014 - All rights reserved.
#
# The copyright to the computer program(s) herein is the property of Ericsson LMI. The programs may be used
# And/or copied only with the written permission from Ericsson LMI or in accordance with the terms and conditions stipulated
# In the agreement/contract under which the program(s) have been supplied.
#
# **************************************************************************************************************
# Name    : batch_runner
# Purpose : Tool that runs a set of commands from a text file for  a given number of iterations.
#           The tool can optionally send a mail to one or many recipient(s) if an error occurs while executing the batch.
# Team    : Blade Runners
# **************************************************************************************************************

"""
batch_runner - Runs a set of specific commands from a text file for a given number of iterations.

It automates the process of executing a set of commands repeatedly and feedback on the result.
It can be found in the /opt/ericsson/enmutils/bin directory. All related log files are located under /var/log/enmutils/ and start with 'batch-'.

Usage:
  batch_runner CMD_FILES NUM_ITERATIONS [--kgb=<kgb>] [--parallel]

Arguments:
  CMD_FILES           Comma separated list of absolute paths to the python files with commands to be run.
  NUM_ITERATIONS      Integer value > 0. It specifies the number of times to execute all commands in the 'CMD_FILES'.

Options:
  --kgb <kgb>         Boolean, default is false, if true, batch runner will assume rpm file locations [default: False]
  --parallel, -p      Run tests in parallel when possible

Examples:
  ./batch_runner /home/user/commands 50
   Runs each command line in the file '/home/user/commands.py' 50 times

  ./batch_runner /var/tmp/perf_tests 1000
   Runs each command line in the file '/var/tmp/perf_tests.py' 1000 times

  ./batch_runner /var/tmp/tests_1,/var/tmp/tests_2,/var/tmp/tests_3 20
   Runs each command line in files '/var/tmp/tests_1, /var/tmp/tests_2 and /var/tmp/tests_3' 20 times

   ./batch_runner /var/tmp/perf_tests 1000 --kgb=True
   Runs each command line in the file '/var/tmp/perf_tests.py' 1000 time, job is executing from rpm KGB+N

   ./batch_runner   /var/tmp/perf_test_1,/var/tmp/perf_test_2 3 --parallel
   Runs commands in both files in parallel three times. Note: No additional validation.

Options:
  -h        Print this help text

Note:
  It is expected that each of the CMD_FILES will specify a variable called: 'commands' that will be a reference to a tuple of tuples as below:
  commands = (
    ('command1', [rc1, rc2], ['list of strings', 'expected', 'to be found', 'in the stdout']),
    ('command2', [rc1, rc2], ['list of strings', 'expected', 'to be found', 'in the stdout']),
  )

  where:
    'command' - Is a string that specifies the full shell command to be run. Use absolute paths.

    [rc1, rc2] - Is a list of the expected return codes after execution of specified command. If the expected return code of a command is 0, no explicit return code needs to be added to the command line. If the expected return code is non-zero, the return code must be supplied in square brackets at the end of the command line. The tool supports providing multiple expected return codes as in some cases it may be desirable to allow a tool or script to return different return codes.To specify more than one return code for a command use a comma-delimited list in square brackets after the command.

    ['list of expected', 'strings']  - Is a list of the expected strings that should be found in the stdout after execution of a command.

"""
import imp
import os
import pkgutil
import signal
import sys
from time import sleep
import unipath
from docopt import docopt

from enmutils.lib.thread_queue import ThreadQueue
from enmutils.lib import init, timestamp, log, exception, filesystem, shell, config

CMD_TIMEOUT = 2700
SLEEP_BETWEEN_CMD_EXECUTION = 5


def execute_batch_runner(cmds_file, num_iterations=1):
    """
    Runs all commands that are listed in a text file for a specific number of times

    :param cmds_file: The absolute path to the file that contains all commands to be run
    :type cmds_file: String
    :param num_iterations: The number of iterations to execute the set of commands in the file
    :type num_iterations: int

    :returns: True if the batch run was a success
    :rtype: boolean
    """

    result = True
    log.log_entry("iterations = " + str(num_iterations) + ")")

    # Get the list of commands to run and make sure that the binaries/scripts exist
    list_of_commands = _get_list_of_commands_from_file(cmds_file).commands

    # Get the current time and print start header
    start_time = timestamp.get_current_time()
    _print_start_header(num_iterations, start_time, list_of_commands)
    iteration_counter = 0
    cmd_counter = 0

    while iteration_counter < num_iterations:
        _print_sub_header(iteration_counter)
        iteration_counter += 1

        for command, return_codes, expected_strings in list_of_commands:
            cmd_counter += 1
            sleep(SLEEP_BETWEEN_CMD_EXECUTION)
            log.logger.info("  File: {4}, command #{0}: {1} {2} {3}".format(
                str(cmd_counter), log.blue_text(command), log.cyan_text(str(return_codes)),
                log.cyan_text(expected_strings), cmds_file.split('/')[-1]))

            response = shell.run_local_cmd(shell.Command(command, timeout=CMD_TIMEOUT, allow_retries=False,
                                                         activate_virtualenv=True))
            if return_codes and response.rc not in return_codes:
                result = False
                log.logger.error("    Command #{0} [ {1} ] from file {2} failed with actual return code "
                                 "of {3} [expected return code(s): {4}.]\n".format(str(cmd_counter),
                                                                                   command, cmds_file,
                                                                                   response.rc, str(return_codes)))
            for expected in expected_strings:
                if expected not in response.stdout:
                    result = False
                    log.logger.info(log.red_text(
                        "    Command #{0} {1} from file {2} failed. Could not find expected string: [ {3} ] "
                        "in response.\n".format(str(cmd_counter), command, cmds_file, expected)))

            if not result:
                log.logger.info(log.red_text("    Response stdout was: {0} ".format(response.stdout)))
                return result

        if len(list_of_commands) != cmd_counter:
            result = False
            log.logger.info(log.red_text(
                '    TOTAL NUMBER OF EXECUTED COMMANDS ({0}) DIFFERS FROM INITIAL NUMBER OF COMMANDS ({1})'.format(
                    cmd_counter, len(list_of_commands))))
            return result

    completion_time = timestamp.get_current_time()
    elapsed_time = timestamp.get_elapsed_time_in_duration_format(start_time, completion_time)

    _print_end_result(num_iterations, completion_time, elapsed_time)
    return result


def _get_list_of_commands_from_file(cmds_file):
    """
    B{Gets the list of commands from the specified commands file}

    @type cmds_file: string
    @param cmds_file: The absolute path to the file that contains all commands to be run.

    :returns: List of commands
    :rtype: list
    """

    d = imp.new_module('commands')
    d.__file__ = cmds_file
    try:
        with open(cmds_file) as config_file:
            exec(compile(config_file.read(), cmds_file, 'exec'), d.__dict__)
    except IOError as e:
        log.logger.error('Unable to load configuration file (%s)' % e.strerror)
    return d


def _print_start_header(num_of_iteration, start_time, list_of_commands):
    """
    B{Prints the start header of the simulation}

    :type num_of_iteration: int
    :param num_of_iteration: The number of iterations to execute the set of commands in the file
    :type start_time: datetime object
    :param start_time: The start time of the simulation
    :type list_of_commands: list
    :param list_of_commands: Commands to be executed
    """

    start_time = str(start_time)[:-7]
    num_of_iteration = str(num_of_iteration)

    log.logger.info(" ")
    log.logger.info(log.cyan_text('COMMANDS TO EXECUTE: {0}'.format(len(list_of_commands))))
    log.logger.info(log.cyan_text('ITERATIONS TO RUN: {0}'.format(num_of_iteration)))
    log.logger.info(log.cyan_text('START TIME: {0}'.format(start_time)))


def _print_sub_header(iteration_counter):
    """
    B{Prints the sub header of the simulation}

    @type iteration_counter: int
    @param iteration_counter: The currently executing  iteration
    """

    iteration_counter = str(iteration_counter + 1)
    log.logger.info(" ")
    log.logger.info(log.purple_text("EXECUTING ITERATION #" + iteration_counter))
    log.logger.info(" ")


def _print_end_result(num_of_iteration, completion_time, elapsed_time):
    """
    B{Prints the end header of the simulation}

    @type num_of_iteration: int
    @param num_of_iteration: The number of iterations to execute the set of commands in the file
    @type completion_time: datetime object
    @param completion_time: The end time of the simulation
    @type elapsed_time: datetime object
    @param elapsed_time: The difference between the start and end time of the simulation
    """

    completion_time = str(completion_time)[:-7]
    elapsed_time = str(elapsed_time).replace(" ", "")
    num_of_iteration = str(num_of_iteration)

    log.logger.info(" ")
    log.logger.info(log.cyan_text("BATCH RUNNER COMPLETED SUCCESSFULLY!!"))
    log.logger.info(log.cyan_text("NUMBER OF ITERATIONS: " + num_of_iteration))
    log.logger.info(log.cyan_text("COMPLETION TIME: " + completion_time))
    log.logger.info(log.cyan_text("TOTAL DURATION: " + elapsed_time))
    log.logger.info(" ")


def _validate_num_of_iterations(num_of_iterations=1):
    """
    B{Validates the user-specified iteration}

    @type num_of_iterations: int
    @param num_of_iterations: The amount of iterations to execute the commands  in the 'cmds_file' file.
    @rtype: int
    @return: num_of_iterations
    """

    try:
        num_of_iterations = int(num_of_iterations)
    except:
        exception.handle_invalid_argument("Number of iterations parameter must be an integer")

    if num_of_iterations < 1:
        exception.handle_invalid_argument("Number of iterations must be greater than 0")

    return num_of_iterations


def _signal_handler(signum, frame):
    """
    B{Register a signal handler with a specific callback function for this tool}

    """

    init.signal_handler(signum, frame, _print_signal_interupt_rc_to_batch_runner_file)


def _print_signal_interupt_rc_to_batch_runner_file():
    """
    B{Writes a return code of 5 to the batch_runner.rc file in the TorUtilities temp directory when someone stops a batch run via the keyboard}

    """

    tor_temp_dir = "/tmp/enmutils"
    output_file = tor_temp_dir + os.sep + "batch_runner.rc"

    filesystem.write_data_to_file("5", output_file)
    init.exit(1)


def _get_module_from_a_file(cmds_file):
    """
    Gets the list of commands from the specified commands file

    :type: cmds_file: string
    :param: cmds_file: The absolute path to the file that contains all commands to be run.
    :returns: Return a new module object called 'cmds'
    :rtype: module object
    """

    d = imp.new_module('cmds')
    d.__file__ = cmds_file
    try:
        with open(cmds_file) as config_file:
            exec(compile(config_file.read(), cmds_file, 'exec'), d.__dict__)
    except IOError as e:
        log.logger.error('Unable to load configuration file (%s)' % e.strerror)
    return d


def get_all_test_files_paths(tests_path, patterns=None):
    """
    Get absolute paths to all test files/scripts in a specified directory matching specified patterns

    :param tests_path: absolute path to directory with batch scripts
    :type tests_path: str
    :param patterns: List of patterns to match with a test file name
    :type patterns: list:

    :return: List of absolute paths to tests that matched specified patterns
    :rtype: list
    """
    filenames = []
    all_files = [f for f in os.listdir(tests_path) if f not in ('internal.py', 'production.py', 'acceptance.py')]

    for pattern in patterns:
        if pattern.lower() == 'all':
            filenames = sorted([os.path.join(tests_path, test).split('commands/')[-1] for test in all_files])
        else:
            filenames.extend(sorted(
                [os.path.join(tests_path, test).split('commands/')[-1] for test in all_files if
                 test.startswith('{0}_test'.format(pattern)) and test.endswith('py')]))
    return filenames


def get_tests_abs_dir_path():
    """
    Get absolute path to directory with batch files/scripts storing the: 'commands' tuple
    :return: Path to a dir with batch tests
    :rtype: file path
    """
    if config.has_prop('KGB_N') and config.get_prop('KGB_N').upper() == "TRUE":
        return "/opt/ericsson/enmutils/.env/lib/python2.7/site-packages/enmutils_int/etc/batch/commands"

    enm_utils_int_path = unipath.Path(pkgutil.get_loader('testslib').filename)
    return enm_utils_int_path.child('batch', 'commands')


def _log_test_order_message(files, msg=''):
    log.logger.info(log.cyan_text(msg + "TESTS ORDER: {0}".format(', '.join(files))))


def get_commands_tuples_for_tools(tools='all'):
    """
    Build a tuple with all batch runner tests and corresponding return codes.
    Tuple is formatted in the way that can be used by batch_runner tool.

    :type: tools: string
    :param: tools: Either 'int' for internal tools or 'prod' for production
    :return:  list of commands
    :rtype: tuple
    """
    batch_tests_path = get_tests_abs_dir_path()
    list_of_commands = []

    # query for all internal batch tests and prepare data structure for batch_runner
    batch_test_files = get_all_test_files_paths(batch_tests_path, [tools])
    _log_test_order_message(batch_test_files)

    for test in batch_test_files:
        cmds = _get_module_from_a_file("{0}/{1}".format(batch_tests_path, test)).commands
        list_of_commands.extend(cmds)

    return list_of_commands


def sort_tests(files):
    """
    Sort tests so that they don't interfere with each other
    :param files: list of all tests to execute
    :type files: list

    :return: Lists of tests to be executed in order, to avoid interference
    :rtype: list
    """
    log.logger.info(log.yellow_text('Sorting tests, please wait..'))

    concurrent = []
    serial = []

    for f in files:
        module = _get_module_from_a_file(f)
        if 'CONCURRENT_RUN' in dir(module) and not module.CONCURRENT_RUN:
            serial.append(f)
        else:
            concurrent.append(f)
    return concurrent, serial


def concurrent_execution(files, num_iterations):
    """
    Execute scripts in parallel.

    :param files: List of abs paths to tests
    :type files: list
    :param num_iterations: Number of Iterations
    :type num_iterations: int

    :return: Boolean indicating True
    :rtype: bool
    """
    log.logger.info(log.cyan_text('Starting concurrent execution of tests: {0} for {1} iteration'.format(', '.join(f for f in files), num_iterations)))

    for _ in range(num_iterations):
        tq = ThreadQueue(files, num_workers=len(files), func_ref=execute_batch_runner, task_join_timeout=60 * 20, task_wait_timeout=60 * 25)
        tq.execute()
    return True


def serial_execution(files, num_iterations):
    msg = 'Starting serial execution of tests for {0} iteration.\n'.format(num_iterations)
    _log_test_order_message(files, msg=msg)

    results = []
    for test_file in files:
        results.append(execute_batch_runner(test_file, num_iterations=num_iterations))
    return results


def cli():
    # Register a signal handler and callback function for interrupts
    """

    :rtype : object
    """
    signal.signal(signal.SIGINT, _signal_handler)

    tool_name = "batch_runner"
    init.global_init("tool", "int", tool_name, sys.argv, execution_timeout=-1)

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
    files = argument_dict['CMD_FILES'].split(',') if argument_dict['CMD_FILES'] else []

    if set(f.lower() for f in files).issubset(set(['int', 'prod', 'all'])):
        files = get_all_test_files_paths(get_tests_abs_dir_path(), files)

    if '--kgb' in argument_dict:
        config.set_prop('KGB_N', argument_dict['--kgb'])

    for test_file in files:
        if not filesystem.does_file_exist(test_file):
            exception.handle_invalid_argument("Specified file: {0} does not exist".format(test_file))

    rc = 1
    try:
        num_iterations = _validate_num_of_iterations(argument_dict['NUM_ITERATIONS'])

        succesful_runs = []
        if num_iterations:
            if argument_dict['--parallel'] and len(files) > 1:
                concurrent, serial = sort_tests(files)

                log.logger.info('CONCURRENT TESTS: {0}. \nSERIAL TESTS: {1}'.format(', '.join([f for f in concurrent]),
                                                                                    ', '.join([f for f in serial])))
                succesful_runs.extend(serial_execution(serial, num_iterations))
                succesful_runs.append(concurrent_execution(concurrent, num_iterations=num_iterations))
            else:
                succesful_runs.extend(serial_execution(files, num_iterations))

        rc = 0 if all(succesful_runs) else rc

    except:
        exception.handle_exception(tool_name)

    init.exit(rc)


if __name__ == '__main__':
    cli()
