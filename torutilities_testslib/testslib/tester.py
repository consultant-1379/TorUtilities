#!/usr/bin/env python
#
# ********************************************************************
#  Ericsson LMI                 Utility Script
#  ********************************************************************
#
# (c) Ericsson LMI 2014 - All rights reserved.
#
# The copyright to the computer program(s) herein is the property of Ericsson LMI. The programs may be used
# and/or copied only with the written permission from Ericsson LMI or in accordance with the terms and conditions stipulated
# in the agreement/contract under which the program(s) have been supplied.
#  ********************************************************************
# Name    : tester.py
# Purpose : Tool that performs source code syntax checking, remote transfer of repo to an MS, and unit/acceptance test execution
# Team    : Blade Runners
# ********************************************************************

"""
Tester - Tool to manage the tests framework

Usage:
  tester.py unit [--modules=<modules>] [--root_path=<root_path>] [--results_path=<results_path>] [--nose_cover_packages=<nose_cover_packages>]  [--cover_min_percentage=<cover_min_percentage>] [--fast] [--profile] [--time]
  tester.py unit <unit_dirs> <results_path> [--nose_cover_packages=<nose_cover_packages>]  [--cover_min_percentage=<cover_min_percentage>] [--fast] [--profile] [--time]
  tester.py acceptance [--root_path=<root_path>] [--results_path=<results_path>] [--modules=<modules>] [--clean-pool] [--skip=<modules>]
  tester.py acceptance <acceptance_dirs> <results_path> [--modules=<modules>] [--clean-pool] [--skip=<modules>]
  tester.py check [--root_path=<root_path>] [--exclude_dirs=<exclude_dirs>] [--staged_files_only] [--docstring]
  tester.py copy <ip> <remote_path> [<common_repo_path>] [--clean]
  tester.py remote-acceptance <ip> <remote_path>
  tester.py view-report
  tester.py object-diff
  tester.py commit-msg MESSAGE

Arguments:
  ip                    IP address of the remote host
  remote_path           Path on the remote machine
  source_dirs           Packages to perform operation on, full paths should be provided
  results_path          Directory in which the results directory will be created
  unit_dirs             Directories of the unit tests
  acceptance_dirs       Directories of the acceptance tests
  root_path             Path to the git repo
  modules               Comma separated list of acceptance modules to test
  MESSAGE               GIT commit message to validate
  skip                  Comma separated list of acceptance modules to skip

Options:
  --fast                Runs the unit tests in fast mode
  --clean               Cleans the directory
  --clean-pool          Cleans the acceptance tests pool
  --profile             Runs the unit tests in profile mode
  --staged_files_only   Only take staged files for checking
  -h, --help            Print this help text

EXAMPLES
    ./tester.py unit
       Executes all of the unit tests
    ./tester.py unit --time
       Executes all unit tests and displays time taken per test, with summary of the tests that take longer than 1s to execute
    ./tester.py unit --fast
       Executes all of the unit tests in parallel without coverage instrumentation (for speed)
    ./tester.py unit --profile
       Executes all of the unit tests; also provides profiling statistics
    ./tester.py acceptance
       Executes all of the acceptance tests locally (Assumes you are on the MS)
    ./tester.py acceptance --modules a_tests_module_name
       Executes the acceptance tests a_tests_module_name locally (Assumes you are on the MS)
    ./tester.py view-report
       Serves the acceptance test report from the local host for remote viewing (only valid after having run the acceptance operation)
    ./tester.py check
       Performs source code analysis to identify any syntax errors, formatting violations or code inefficiencies
    ./tester.py check --docstring
       Performs additional checks on docstring to verify syntax
    ./tester.py commit
       Performs source code checks and unit tests; same as running './tester.py check' and './tester.py unit' in that order
    ./tester.py copy 1.2.3.4 /path/to/code
       Copies the ENM Utilities code repository to the specified location on the remote host
    ./tester.py copy 1.2.3.4 /path/to/code --clean
       Copies the ENM Utilities code repository to the specified location on the remote host, deleting directory /path/to/code before copying the code
    ./tester.py remote-acceptance 1.2.3.4 /path/to/code
       Copies the ENM Utilities code repository to the specified location and run acceptance tests
    ./tester.py object-diff
       Checks if changes have been made to critical modules (i.e. enm_node, profile, load_node etc) and if library modules have been renamed or deleted. Files must be added with git add.

Note:
  Using special characters in the value of arguments KEY, VALUE and TOKEN is generally allowed, but to be safe and avoid
  unwanted shell globbing, it is recommended to surround the value with single quotes.

  The value of argument TOKEN cannot start with a dash character -
"""
import os
import re
import signal
import commands

from docopt import docopt
from enmutils.lib import init, log
from enmutils.lib.exceptions import ValidationError
from enmutils_int.lib import test
from enmutils_int.lib.common_utils import STORAGE_DIR
from enmutils_int.lib.fabfile import run_acceptance
from fabric.tasks import execute

COPY_PREFIX_PATH = '{0}/bladerunners'.format(STORAGE_DIR)


def _get_test_dirs(base_path, test_type='unit'):
    """
    Function to find the directories containing the required test types

    :param base_path: The root directory path to execute find command
    :type base_path: str
    :param test_type: Type of tests to be identified for example unit, acceptance
    :type test_type: str

    :return: List of detected test directories
    :rtype: list
    """
    rc, output = commands.getstatusoutput('find {0} -path "*/tests/{1}"'.format(base_path, test_type))
    if rc:
        raise ValidationError('No unit tests dirs found, please pass them using --unit_dirs option')
    return [path.strip() for path in output.split('\n') if path]


def _get_git_repo():
    """
    Function to determine the git repo path

    :return: The path to the git repo
    :rtype: str
    """
    rc, output = commands.getstatusoutput('git rev-parse --show-toplevel')
    if rc:
        raise ValidationError('Not a git repo, please run this tool inside the git repo or provide explicit '
                              '--root_path option')
    return output.strip()


def check_exist(paths, name):
    """
    Checks if the modules are in the unit test directories

    :param paths: The path for the directory
    :type paths: list
    :param name: The names of modules to check for
    :type name: list
    :return: List of modules not found
    :rtype: list
    """

    check_list = name.split(",")
    # If the modules does not start with "u_tests_" then "u_tests_" will be added
    # If the modules does not end with ".py" then ".py" will be added
    for module in check_list:
        index = check_list.index(module)
        if not module.endswith(".py"):
            check_list[index] = check_list[index]+".py"
        if not module.startswith("u_tests_"):
            check_list[index] = "u_tests_"+check_list[index]
    temp_list = check_list[:]
    for path in paths:
        for _, _, files in os.walk(path):
            for module in temp_list:
                if module in files and module in check_list:
                    check_list.remove(module)
    return check_list


def _validate_commit_msg(message):
    """
    Confirm  git commit message adheres to the correct patten

    :param message: The commit message value
    :type message: str
    :return: Boolean result of the check
    :rtype: int
    """
    pattern = r'(^TORF-[0-9]+ |^RTD-[0-9]+ |^NO JIRA )'
    if not re.match(pattern, message):
        log.logger.error("Aborting commit. Your commit message [{0}] is invalid.\nMessage must start, one of {1}"
                         .format(message, pattern))
        return 1
    return 0


def cli():
    arguments = docopt(__doc__)

    signal.signal(signal.SIGINT, init.signal_handler)
    init.global_init("tester", "int", 'tester', execution_timeout=4000)

    # Sane defaults
    unit_dirs = cover_packages = None
    profile_code, fast_unit_tests = bool(arguments['--profile']), bool(arguments['--fast'])
    cover_min_percentage = int(arguments['--cover_min_percentage']) if arguments['--cover_min_percentage'] is not None else 100
    show_time_taken_per_testcase = arguments['--time']

    if arguments['--nose_cover_packages'] is not None:
        cover_packages = [p.strip() for p in arguments['--nose_cover_packages'].split(',')]
    if arguments['--root_path']:
        root_path = os.path.abspath(arguments['--root_path'])
    else:
        try:
            root_path = _get_git_repo()
        except ValidationError as e:
            log.logger.warn(str(e))
            init.exit(1)
    results_path = arguments['<results_path>'] or arguments['--results_path'] or root_path
    modules = arguments.get('--modules', [])

    if arguments['acceptance']:
        if arguments['<acceptance_dirs>'] is not None:
            a_dirs = [d.strip() for d in arguments['<acceptance_dirs>'].split(',')]
        else:
            a_dirs = _get_test_dirs(root_path, test_type='acceptance')
        rc = test.execute_tests(
            a_dirs, results_path, "acceptance", clean_pool=bool(arguments['--clean-pool']), modules=modules,
            skip_modules=arguments['--skip'])
    elif arguments['unit']:
        if arguments['<unit_dirs>']:
            unit_dirs = [d.strip() for d in arguments['<unit_dirs>'].split(',')]
        else:
            try:
                unit_dirs = _get_test_dirs(root_path)
            except ValidationError as e:
                log.logger.warn(str(e))
                init.exit(1)
        if modules:
            modules_not_found = check_exist(unit_dirs, modules)
            if modules_not_found:
                print("The following modules cannot be found:{0} ".format(modules_not_found))
                return
        rc = test.execute_unit_tests(
            unit_dirs, results_path, profile_code, fast_unit_tests, show_time_taken_per_testcase,
            nose_cover_packages=cover_packages, cover_min_percentage=cover_min_percentage, modules=modules)
    elif arguments['check']:
        if arguments['--exclude_dirs']:
            exclude_dirs = [d.strip() for d in arguments['--exclude_dirs'].split(',')]
        else:
            exclude_dirs = []
        exclude_dirs.extend(['deprecated', 'schedules'])
        rc = test.check_source_code(root_path, exclude_dirs=exclude_dirs,
                                    staged_files_only=arguments['--staged_files_only'],
                                    pylint_docstring_check=arguments['--docstring'])
    elif arguments['view-report']:
        rc = test.display_allure_report(results_path)
    elif arguments['commit-msg']:
        rc = _validate_commit_msg(arguments['MESSAGE'])
    elif arguments['copy']:
        if not os.path.isabs(arguments['<remote_path>']):
            remote_path = os.path.join(COPY_PREFIX_PATH, arguments['<remote_path>'])
        else:
            remote_path = arguments['<remote_path>']
        rc = test.copy(arguments['<ip>'], remote_path, bool(arguments['--clean']), common_repo_path=arguments['<common_repo_path>'])
    elif arguments['remote-acceptance']:
        user_host = '%s@%s' % (test.DEFAULT_USER, arguments['<ip>'])
        results = execute(run_acceptance, remote_dir=arguments['<remote_path>'], host=user_host)
        rc = int(bool(results))
    elif arguments['object-diff']:
        rc = test.object_diff(root_path)

    init.exit(rc)


if __name__ == "__main__":
    cli()
