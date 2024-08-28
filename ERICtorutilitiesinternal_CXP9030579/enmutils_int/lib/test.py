# ********************************************************************
# Name    : Test
# Summary : Functional module which provide TESTER tool functionality.
#           Responsible for all areas of unit and acceptance test
#           management, including coverage and report generation, also
#           provides the functionality for PEP8,Pylint and DOS2UNIX
#           testing.
# ********************************************************************

import StringIO
import commands
import datetime
import multiprocessing
import os
import pkgutil
import pstats
import random
import re
import subprocess
import sys
import time
from copy import deepcopy
from time import strftime

import unipath

from enmutils.lib import log, filesystem, shell, persistence
from enmutils.lib.exceptions import InvalidOpenapiFormat
from enmutils_int.lib import netsim_executor
from enmutils_int.lib.common_utils import STORAGE_DIR
from enmutils_int.lib.enm_user import get_workload_admin_user
from enmutils_int.lib.netsim_operations import PowerNodes
from enmutils_int.lib.nrm_default_configurations.basic_network import TIME_KEYS
from enmutils_int.lib.nrm_default_configurations.profile_values import networks
from enmutils_int.lib.services.swagger_ui import OPENAPI_DIR, get_url_view_function_map
from enmutils_int.lib.shm_utilities import SHMLicense
from testslib import test_utils
from testslib.test_fixture import TestFixture

WORKER_PRINT_LOCK = multiprocessing.Lock()

RESULTS_DIR = "test-results"
DEFAULT_USER = 'root'
NOSETESTS_PATH = os.path.join(os.path.dirname(sys.executable), "nosetests")

ENMUTILS_INT_PATH = unipath.Path(pkgutil.get_loader('enmutils_int').filename)
TESTS_PATH_INT = unipath.Path(pkgutil.get_loader('testslib').filename)
FABFILE = ENMUTILS_INT_PATH.child('lib', 'fabfile.py')
COVERAGE_RC_FILE = os.path.abspath(os.path.join(TESTS_PATH_INT, "etc", "tester", "coverage.rc"))

# ALLURE
ALLURE_DIR = "/home/enmutils/allure"
ALLURE_BAT = os.path.join(ALLURE_DIR, "bin", "allure")
ALLURE_ARCHIVE = os.path.join(TESTS_PATH_INT, "etc", "tester", "allure-commandline.tar.gz")
ENVIRONMENT_XML = os.path.join(TESTS_PATH_INT, "etc", "tester", "environment.template")
ALLURE_REPORT_GENERATION_CMD = "{0} report generate \"{1}\" -o \"{2}\""
SERVE_ALLURE_REPORT_CMD = "{0} report open -o \"{1}\""
ALLURE_TEST_CMD = NOSETESTS_PATH + " --nologcapture --with-allure --logdir={0} {1}"
ALLURE_RESULT_THREAD_UPDATE_CMD = """find {0} -name \"*-testsuite.xml\" -print | xargs perl -i -pe \"s|<labels/>|<labels><label name=\\"thread\\" value=\\"root\\@localhost.{1}({2})\\"/></labels>|g\""""
ALLURE_RESULTS_DIR = os.path.join(RESULTS_DIR, "allure-results")

# UNIT TESTS
# more about below flags here: http://nose.readthedocs.io/en/latest/usage.html#extended-usage
FAST_UNIT_TEST_CMD = NOSETESTS_PATH + " -v -d --exe --processes=-1 {dirs}"
UNIT_TEST_CMD = NOSETESTS_PATH + " -v -d --exe --with-coverage --cover-min-percentage={cover_min_percentage} --cover-package={packages} --cover-erase --cover-branches --cover-config-file={cover_config_path} {timer_options} {dirs}"
UNIT_SINGLE_TEST_CMD = NOSETESTS_PATH + " -v -d --exe  --tests={modules} --with-coverage --cover-min-percentage={cover_min_percentage} --cover-package={packages} --cover-erase --cover-branches --cover-config-file={cover_config_path} {timer_options} "
PROFILED_UNIT_TEST_CMD = NOSETESTS_PATH + " -v -d --exe --with-coverage --cover-min-percentage={cover_min_percentage} --cover-package={packages} --cover-erase --cover-branches --cover-config-file={cover_config_path} --with-cprofile --cprofile-stats-erase --profile-stats-file={stats_file} {dirs}"

# COVERAGE COMMAND
COVERAGE_CMD = "coverage combine; coverage html -d {html_dir} -i --omit=*test.py,*fabfile.py,*default_configurations*,*deprecated*,*__init__.py,*enm_role.py,{accept_tests}"

# PEP CHECKS
PEP_CHECK_CMD = "pep8 --ignore=E501,W601,E401 {0}"

# PYLINT CHECKS
PYLINT_RC_FILE = os.path.abspath(os.path.join(TESTS_PATH_INT, "etc", "tester", "pylint.rc"))
PYLINT_LOAD_PLUGINS = "pylint.extensions.docparams"
PYLINT_CHECK_CMD = "pylint --load-plugins={0} --rcfile={1} {2}"

# MAX WORKERS (This is the number of test processes that will run in parallel)
MAX_WORKERS = 16
CHUNK_SIZE = None
RESULTS_PATH = ''

# COLOR TEXT
RED_TEXT = '\033[91m'
GREEN_TEXT = '\033[92m'
PURPLE_TEXT = '\033[95m'
YELLOW_TEXT = '\033[33m'
NORMAL_TEXT = '\033[0m'

IGNORED_FILES = ['__init__.py', 'tester.py', 'test.py', '/lib/schedules']
COMMON_LIB = "enmutils/lib"
INTERNAL_LIB = "enmutils_int/lib"
FILES_TO_CHECK = "enm_node.py,enm_role.py,enm_user_2.py,load_node.py,profile.py"

BASELINE_RPM = "4.56.11"

# Used for nose-timer plugin
TIMER_OK_LIMIT = "1s"
TESTER_OUTPUT_DIVS = "*" * 40

######################
# SOURCE CODE CHECKS #
######################


def _get_modified_python_files(git_repo_dir):
    """
    Return a list of all modified files in the repo

    :param git_repo_dir: path to the git repository root
    :rtype: list[string]

    """

    (rc, stdout) = _execute_command("cd {0}; git diff --cached --name-status".format(os.path.abspath(git_repo_dir)))
    if rc:
        raise RuntimeError("Could not get list of modified files ({rc}): {error}".format(rc=rc, error=stdout))

    modified_files = set()
    for line in stdout.strip().splitlines():
        modification_type, file_path = line.split()[:2]
        if len(line.split()) == 3:
            file_path = line.split()[2]
        if modification_type != "D" and file_path.endswith(".py") and not any(f in file_path for f in IGNORED_FILES):
            modified_files.add(os.path.abspath(file_path))

    return modified_files


def _get_acceptance_tests(dirs, modules=None, unit=None, skip_modules=None):
    """
    Gets all acceptance tests if none specified in modules

    :param dirs: list of directories to look for acceptance tests
    :param modules: comma separated list of test modules
    :type unit: bool
    :param unit: Flag indicating that the modules are unit tests
    :param skip_modules: Comma separated list of test modules to be skipped
    :type skip_modules: str

    :return: acceptance tests list
    """
    tests = []
    acceptance_prefix = "a_tests_" if not unit else "u_tests_"
    if modules:
        module_names = [acceptance_prefix + module if acceptance_prefix not in module else module for module in modules.split(",")]
    else:
        module_names = [acceptance_prefix]

    for dirname in dirs:
        for module_name in module_names:
            filtered = _get_filtered_files(dirname, filter_name=lambda file_name, m=module_name: file_name.startswith(m) and file_name.endswith(".py"))
            tests.extend(filtered)
    if skip_modules:
        tests = _remove_acceptance_tests_to_skipped(skip_modules.split(','), acceptance_prefix, tests)
    return list(set(tests))


def _remove_acceptance_tests_to_skipped(modules_to_skip, acceptance_prefix, tests):
    """
    Remove any matching test paths matching tests to be skipped

    :param modules_to_skip: List of module names to skip
    :type modules_to_skip: list
    :param acceptance_prefix: Naming prefix of acceptance tests
    :type acceptance_prefix: str
    :param tests: List of test paths discovered
    :type tests: list

    :return: List of updated test paths after removing matching tests to be skipped
    :rtype: list
    """
    updated_modules = []
    for module_name in modules_to_skip:
        if not module_name.startswith(acceptance_prefix):
            module_name = acceptance_prefix + module_name
        if not module_name.endswith(".py"):
            module_name = module_name + ".py"
        updated_modules.append(module_name)
    for module_to_skip in updated_modules:
        for test in tests[:]:
            test_name = test.split("/")[-1]
            if test_name == module_to_skip:
                log.logger.info("Skippping test\t[{0}]".format(test_name))
                tests.remove(test)
    return tests


def _get_all_python_files_in_repo(root_path, exclude_dirs=None):
    """
    Build a list of the python modules we want to check in the local repository

    :param root_path: root path to walk to discover Python source modules
    :param exclude_dirs: list of directory paths to exclude

    :return: A tuple where: index 0 is a boolean indicating whether Windows line endings were found; index 1 is a message to be displayed on error
    :rtype: Tuple

    """

    python_files = []
    if exclude_dirs is None:
        exclude_dirs = []

    def filter_name(file_name):
        return file_name.endswith(".py") and not any(f in file_name for f in IGNORED_FILES)

    filtered = _get_filtered_files(root_path, filter_name=filter_name, exclude_dirs=exclude_dirs)
    python_files.extend(filtered)
    return python_files


def _get_filtered_files(directory, filter_name, exclude_dirs=None):
    """
    :param directory: path to the directory
    :param filter_name: callable for filtering the paths, must take single arg file name
    :exclude_dirs: list of directory names to be excluded
    """
    filtered = []

    for (dirpath, dirnames, files) in os.walk(directory):
        if exclude_dirs is not None:
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs and not d.startswith('.')]
        for file_name in files:
            if filter_name(file_name):
                filtered.append(os.path.abspath(os.path.join(dirpath, file_name)))

    return filtered


def _check_line_endings(file_name):
    """
    Checks if any files in the list contain Windows line endings

    :param file_name: Absolute path of the file to be checked
    :type file_name: string

    :return: A tuple where: index 0 is a boolean indicating whether Windows line endings were found; index 1 is a message to be displayed on error
    :rtype: Tuple

    """

    found_windows_lines = False
    msg = ""

    (rc, _) = _execute_command("file {0} | grep -E 'CRLF line terminators|\015'".format(file_name))
    if rc == 0:
        msg = "ERROR: File {0} has Windows line endings".format(file_name)
        found_windows_lines = True

    return (found_windows_lines, msg)


def check_line_endings(files_to_check):
    """
    Checks source code modules for UNIX line terminators

    :param files_to_check: List of absolute file paths of source modules to be checked
    :type files_to_check: list

    :rtype: boolean

    """

    line_ending_result = True

    print "\n**************************************"
    print "* CHECKING FOR UNIX LINE TERMINATORS *"
    print "**************************************\n"

    # Create a pool of processes to execute the modules
    return_tuples = _pool(_check_line_endings, files_to_check)

    for return_tuple in return_tuples:
        if return_tuple[0]:
            line_ending_result = False
            print "{0}{1}{2}".format(RED_TEXT, return_tuple[1], NORMAL_TEXT)

    if line_ending_result:
        print "{0}All modules have UNIX line terminators{1}".format(GREEN_TEXT, NORMAL_TEXT)
    else:
        print "\n{0}One or more modules does not have proper UNIX line terminators{1}".format(RED_TEXT, NORMAL_TEXT)

    return line_ending_result


def _execute_pep_check(file_name):
    """
    Checks each source file for PEP violations

    :param file_name: Absolute path of the file to be checked
    :type file_name: string

    :return: Tuple where: index 0 is a boolean indicating whether check was successful or not; index 1 is a message to be displayed on error
    :rtype: Tuple

    """

    check_successful = False
    msg = ""

    (rc, stdout) = _execute_command(PEP_CHECK_CMD.format(file_name))

    if rc == 0:
        check_successful = True
    else:
        msg = "{0}PEP8 checks for file {1} failed:\n{2}{3}".format(RED_TEXT, file_name, NORMAL_TEXT, stdout)

    return (check_successful, msg)


def execute_pep_checks(files_to_check):
    """
    Checks source code modules for PEP code format violations

    :param files_to_check: List of absolute file paths of source modules to be checked
    :type files_to_check: list

    :return: Whether the pep checks ran or not
    :rtype: boolean

    """

    pep_result = True

    print "\n******************************************"
    print "* CHECKING FOR PEP FORMATTING VIOLATIONS *"
    print "******************************************\n"

    # Create a pool of processes to execute the modules
    return_tuples = _pool(_execute_pep_check, files_to_check)

    for return_tuple in return_tuples:
        if not return_tuple[0]:
            pep_result = False
            print return_tuple[1]

    if pep_result:
        print "{0}All module PEP checks have passed{1}".format(GREEN_TEXT, NORMAL_TEXT)
    else:
        print "\n{0}One or more module have PEP code formatting violations{1}".format(RED_TEXT, NORMAL_TEXT)

    return pep_result


def _execute_pylint_check(pylint_input_data):
    """
    Checks each source file for Pylint syntax violations

    :param pylint_input_data: Tuple containing string (absolute path of the file to be checked) and boolean (to indicate if docstring check to be performed or not)
    :type pylint_input_data: tuple

    :return: Whether the pylint checks ran or not
    :rtype: Tuple where: index 0 is a boolean indicating whether check was successful or not; index 1 is a message to be displayed on error

    """

    check_successful = False
    msg = ""

    file_name, pylint_docstring_check = pylint_input_data

    load_plugins = PYLINT_LOAD_PLUGINS if pylint_docstring_check else ""
    (rc, stdout) = _execute_command(PYLINT_CHECK_CMD.format(load_plugins, PYLINT_RC_FILE, file_name))

    if rc == 0:
        check_successful = True
    else:
        msg = "{0}Pylint checks for file {1} failed:\n{2}{3}".format(RED_TEXT, file_name, NORMAL_TEXT, stdout)

    return (check_successful, msg)


def execute_pylint_checks(files_to_check, pylint_docstring_check):
    """
    Checks source code modules for Pylint syntax violations

    :param files_to_check: List of absolute file paths of source modules to be checked
    :type files_to_check: list
    :param pylint_docstring_check: bool to indicate if extra docstring checks are to be performed
    :type pylint_docstring_check: bool

    :return: True or False whether the checks ran or not
    r:type: boolean

    """

    pylint_result = True

    print "\n*****************************************"
    print "* CHECKING FOR PYLINT SYNTAX VIOLATIONS *"
    print "*****************************************\n"

    # Create a pool of processes to execute the modules
    pylint_input = zip(files_to_check, [pylint_docstring_check for _ in files_to_check])
    return_tuples = _pool(_execute_pylint_check, pylint_input)

    for return_tuple in return_tuples:
        if not return_tuple[0]:
            pylint_result = False
            print return_tuple[1]

    if pylint_result:
        print "{0}All module Pylint checks have passed{1}".format(GREEN_TEXT, NORMAL_TEXT)
    else:
        print "\n{0}One or more module have Pylint syntax violations{1}".format(RED_TEXT, NORMAL_TEXT)

    return pylint_result


#########################
# COMMON TEST FUNCTIONS #
#########################
def _execute_test(test_module):
    """
    Run a single acceptance test module using an available test index

    :param test_module: The name of the test module to execute
    :type test_module: string

    :return: The return code from function "_execute_command"
    :rtype: int

    """

    # If this is the first test executed by this process, sleep for a small, random amount of time
    if "TEST_SLEEP_DONE" not in os.environ:
        time.sleep(random.random())
        os.environ["TEST_SLEEP_DONE"] = "TEST_SLEEP_DONE"

    # Get what we need to create the full allure test command (test name and results dir)
    module_name = os.path.basename(test_module).replace(".py", "")

    result_dir = os.path.join(RESULTS_PATH, ALLURE_RESULTS_DIR, module_name)

    cmd = ALLURE_TEST_CMD.format(result_dir, test_module)

    WORKER_PRINT_LOCK.acquire()
    print "Executing test module {0}{1}{2} [PID {3}]...".format(PURPLE_TEXT, module_name, NORMAL_TEXT, os.getpid())
    WORKER_PRINT_LOCK.release()

    try:
        # Get an available test DB index from the index pool
        index = (persistence.NODE_POOL_DB_INDEX if "a_tests_workload_ops" in test_module
                 else test_utils.get_test_db_index())

        # Set an environment variable indicating which DB test index the worker process should use
        cmd = "export REDIS_DB_INDEX={0}; {1}".format(index, cmd)

        # Execute the test
        (rc, output) = _execute_command(cmd)
    finally:
        # Return the test DB index to the index pool
        test_utils.return_test_db_index(index)

    # Update the result XML file with the name of the module for the timeline
    cmd = ALLURE_RESULT_THREAD_UPDATE_CMD.format(result_dir, module_name, os.getpid())
    (_, dummy) = _execute_command(cmd)

    WORKER_PRINT_LOCK.acquire()
    if rc == 0:
        print "{0}  Test module {1} finished with return code {2} [PID {3}]...{4}".format(GREEN_TEXT, test_module, rc, os.getpid(), NORMAL_TEXT)
    else:
        print "{0}  Test module {1} finished with return code {2} [PID {3}]...{4}".format(RED_TEXT, test_module, rc, os.getpid(), NORMAL_TEXT)

        if rc != 1 and output is not None and len(output) > 0:
            print "\n{0}\n".format(output)
    WORKER_PRINT_LOCK.release()

    # Return the rc so that the main process can determine if everything ran fine or not
    return rc


def _generate_allure_report(results_dir):
    """
    Generates the Allure report from all of the test result XML files

    :rtype: None

    """
    extract_allure_commandline_archive()
    result = False

    # Build the absolute paths
    xml_path = os.path.abspath(os.path.join(results_dir, ALLURE_RESULTS_DIR))
    report_path = os.path.abspath(os.path.join(results_dir, RESULTS_DIR, "report"))
    jar_path = os.path.abspath(ALLURE_BAT)

    cmd = ALLURE_REPORT_GENERATION_CMD.format(jar_path, xml_path, report_path)

    (rc, stdout) = _execute_command(cmd)

    if rc == 0:
        print("Allure report generated successfully")
        print("\nReport can be found at {0}{1}{2}".format(PURPLE_TEXT, report_path, NORMAL_TEXT))
        print("Acceptance test report can be served for local or remote viewing by re-runnng the tester tool with "
              "the {0}view-report{1} operation\n".format(PURPLE_TEXT, NORMAL_TEXT))
        result = True
    else:
        print("{0}ERROR: Could not generate Allure report{1}".format(RED_TEXT, NORMAL_TEXT))
        print(stdout)

    return result


def _update_environment_info(results_dir):
    """
    Adds information to the Allure report about the test environment, code versions, etc.

    :rtype: None

    """

    # Read in the template environment.xml
    file_contents = None
    with open(ENVIRONMENT_XML, "r") as handle:
        file_contents = handle.read()

    if file_contents is not None:
        # Fetch the values we want to inject into the report
        (_, hostname) = _execute_command("hostname -f")
        hostname = hostname.strip()

        (_, ms_ip) = _execute_command("/sbin/ifconfig eth0 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}'")
        if not ms_ip:
            (_, ms_ip) = _execute_command("/sbin/ifconfig br0 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}'")

        # Get the ENM ISO version
        (rc, enm_build) = _execute_command("find /var/tmp -name ERICenm_CXP*.iso -print | sort | grep -E '[0-9]+.[0-9]+.[0-9]+.iso' | tail -1 | sed -e 's/.*-//g' | sed -e 's/.iso//g'")
        if rc == 0 and len(enm_build) > 0:
            enm_build = enm_build.strip()
            file_contents = file_contents.replace("%%build%%", enm_build)
        else:
            # If we couldn't get the ISO version from the above directory try this one
            (rc, enm_build) = _execute_command("find /software/autoDeploy -name ERICenm_CXP*.iso -print | sort | grep -E '[0-9]+.[0-9]+.[0-9]+.iso' | tail -1 | sed -e 's/.*-//g' | sed -e 's/.iso//g'")
            enm_build = enm_build.strip()
            file_contents = file_contents.replace("%%build%%", enm_build)

        # Get the LITP ISO version
        (rc, litp_build) = _execute_command("find /var/tmp -name ERIClitp*.iso -print | sort | grep -E '[0-9]+.[0-9]+.[0-9]+.iso' | tail -1 | sed -e 's/.*-//g' | sed -e 's/.iso//g'")
        if rc == 0 and len(litp_build) > 0:
            litp_build = litp_build.strip()
            file_contents = file_contents.replace("%%litp_build%%", litp_build)
        else:
            # If we couldn't get the ISO version from the above directory try this one
            (rc, litp_build) = _execute_command("find /software/autoDeploy -name ERIClitp*.iso -print | sort | grep -E '[0-9]+.[0-9]+.[0-9]+.iso' | tail -1 | sed -e 's/.*-//g' | sed -e 's/.iso//g'")
            litp_build = litp_build.strip()
            file_contents = file_contents.replace("%%litp_build%%", litp_build)

        base_dir = os.path.abspath(os.path.join(ENMUTILS_INT_PATH, "..", ".."))

        (rc, rpm_version) = _execute_command("rpm -qa | grep ERICtorutilities_CXP")
        if rc == 0:
            version = re.search('-([0-9]*.[0-9]*.[0-9]*)', rpm_version)
            file_contents = file_contents.replace("%%rpm_version%%", version.group(1))

        # Get the current date for the report
        current_time = strftime("%m-%d-%Y %H:%M:%S")

        # Replace the templated values with actual values
        file_contents = file_contents.replace("%%hostname%%", hostname).replace("%%directory%%", base_dir).replace("%%date%%", current_time).replace("%%ms_ip%%", ms_ip)

        # Write the file out into the Allure XML directory
        with open(os.path.join(results_dir, ALLURE_RESULTS_DIR, "environment.xml"), "w") as handle:
            handle.write(file_contents)


def _clear_test_results_dir(results_dir):
    """
    Clears the test results directory before running tests

    :rtype: None

    """

    # Clear out the test results directory
    msg = "Clearing test results directory {0}{1}{2}\n".format(PURPLE_TEXT, RESULTS_DIR, NORMAL_TEXT)
    if log.logger is not None:
        log.logger.info(msg)
    else:
        print msg
    _execute_command("rm -rf {0}/*".format(os.path.abspath(os.path.join(results_dir, RESULTS_DIR))))


def _execute_command(cmd):
    """
    Run a local command and return the rc and stdout

    :param cmd: The local command to be run as a python subprocess
    :type cmd: string

    :return: Tuple where index 0 is return code and index 1 is stderr merged into stdout
    :rtype: Tuple

    """

    log.logger.debug("Running local command '{0}'".format(cmd))
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, close_fds=True)
    stdout = process.communicate()[0]
    process.stdout.close()
    return process.returncode, stdout


def _pool(target, work_items, test_pool_timeout=None, max_num_test_processes=None, chunk_size=None):
    """
    Creates a worker pool to work through the passed work items in parallel

    :param target: Callable to be invoked by each worker for each work item
    :type target: callable
    :param max_num_test_processes: Maximum number of processes to create for testing executions
    :type max_num_test_processes: int
    :param work_items: List of work items; each invocation of the target callable will be passed one value from this list
    :type work_items: list
    :param test_pool_timeout: integer timeout value within which the test suite should complete
    :type test_pool_timeout: int

    :return: List of results returned from each invocation of the callable
    :rtype: list

    """

    # Figure out how many workers we need
    pool_size = (multiprocessing.cpu_count() * 4)
    if len(work_items) < pool_size:
        pool_size = len(work_items)

    # Check if we are overriding max workers in props
    if max_num_test_processes:
        pool_size = max_num_test_processes
    else:
        # Make sure we don't exceed the maximum number of workers
        if pool_size > MAX_WORKERS:
            pool_size = MAX_WORKERS

    log.logger.debug("Creating pool size of {0} processes to run tests".format(pool_size))
    pool = multiprocessing.Pool(pool_size)
    if not test_pool_timeout:
        test_timeout = 4000
    try:
        results_to_check = pool.map_async(target, work_items, chunksize=chunk_size)
        return results_to_check.get(test_timeout)
    except multiprocessing.TimeoutError:
        log.logger.error("\n{0}ERROR: Test execution pool has exceeded timeout of {1}s{2}".format(RED_TEXT, test_timeout, NORMAL_TEXT))
        print "\n{0}ERROR: Test execution pool has exceeded timeout of {1}s{2}".format(RED_TEXT, test_timeout, NORMAL_TEXT)
        return [1]
    finally:
        pool.terminate()
        pool.join()


########
# COPY #
########

def _check_passwordless_access(remote_ms, port=22):
    """
    Checks if the client has passwordless access to the remote MS

    :param remote_ms: The IP of the remote MS
    :type remote_ms: string

    :return True or False whether passwordless access is available to the client
    :rtype: boolean

    """
    result = False

    ssh_cmd = "/usr/bin/ssh -p {0} -o PreferredAuthentications=publickey -o ConnectTimeout=5 -o StrictHostKeyChecking=no {1}@{2} ls".format(port, DEFAULT_USER, remote_ms)
    (rc, _) = _execute_command(ssh_cmd)
    if rc == 0:
        result = True

    return result


##############################
# PUBLIC OPERATION FUNCTIONS #
##############################

def copy(remote_host, remote_dir, clean_remote_dir, common_repo_path=None):
    """
    Copies source code from the local git repository to the specified directory on the remote host

    :param remote_host: IP address or hostname of remote host. If you want to connect to a specific port use xx.xx.xx.xx:<Port>
    :type remote_host: string
    :param remote_dir: Absolute path of the directory on the remote host that the local code repository will be copied to
    :type remote_dir: string
    :param clean_remote_dir: Flag controlling whether remote directory is deleted before code is copied over
    :type clean_remote_dir: boolean

    :return: A return code (0 on success; 1 on copy fail; 2 if remote host is not available)
    :rtype: int

    """

    host, port = remote_host, 22
    if ':' in remote_host:
        host, port = remote_host.split(':')

    if not _check_passwordless_access(host, port):
        print """Couldn't gain access to the remote host: {1} on port: {2}. You need passwordless access to copy files.
        Run: 'ssh-copy-id {0}@{1}' for Physical machine and: 'ssh-copy-id -p 2242 {0}@{1}' when using a vApp.""".format(DEFAULT_USER, host, port)
        return 2

    # Note that when the below command is executed, the deploy function within the fabfile.py will be called, with the parameters
    cmd = "fab -f {0} -H {1}@{2}:{3} deploy:remote_dir={4},clean={5}".format(FABFILE, DEFAULT_USER, host, port, remote_dir, clean_remote_dir)
    if common_repo_path:
        cmd = cmd + ',common_repo=%s' % common_repo_path
    print "\nCopying local repository to {0} on remote MS {1}...".format(remote_dir, host)

    (rc, stdout) = _execute_command(cmd)
    if rc == 0:
        print "\nSuccessfully copied repository to {0}{1}{2} on the remote MS".format(PURPLE_TEXT, remote_dir, NORMAL_TEXT)
        print "Run {0}source {1}/.env/bin/activate{2} on the MS to activate the virtual environment".format(PURPLE_TEXT, remote_dir, NORMAL_TEXT)
    else:
        print "\n{0}Unable to copy repo to {1} on the remote MS.{2}\n{3}".format(RED_TEXT, remote_dir, NORMAL_TEXT, stdout)
        rc = 1

    return rc


def check_source_code(git_repo, exclude_dirs=None, staged_files_only=False, pylint_docstring_check=False):
    """
    Checks source code modules for syntax and formatting errors

    :param git_repo: path to the git root directory
    :type git_repo: str
    :param exclude_dirs: names of the directories to exclude from the check
    :type exclude_dirs: list
    :param staged_files_only: bool indicating if we need to perform check on commited files only
    :type staged_files_only: bool
    :param pylint_docstring_check: bool indicating if pylint plugin will be loaded to check docstring
    :type pylint_docstring_check: bool

    :return: Return code (0 on success; 1 on fail)
    :rtype: int
    """

    # Build a list of all of the files in the repository we want to check
    if staged_files_only:
        files_to_check = _get_modified_python_files(git_repo)
    else:
        files_to_check = _get_all_python_files_in_repo(git_repo, exclude_dirs=exclude_dirs)

    if not files_to_check:
        log.logger.warn('No files to check, will not perform the checks')
        return 0

    # Run the checks and bail when we hit the first fail
    if not check_line_endings(files_to_check):
        return 1

    if not execute_pep_checks(files_to_check):
        return 1

    if not execute_pylint_checks(files_to_check, pylint_docstring_check):
        return 1

    if not validate_open_api_specification():
        return 1

    if not check_missing_keys():
        return 1

    if staged_files_only and check_staged_files_for_sleep_function(files_to_check):
        check_sleep_attribute_available(files_to_check)

    # If we didn't fail and return above, all checks have passed
    return 0


def _get_subset_of_tests_from_list(test_modules, module_subset):
    """
    Checks if any of the required tests are specified in the list of modules found

    :param test_modules: a list of test modules
    :type test_modules: list
    :param module_subset: a list of modules
    :type module_subset: list

    :return: A List of subset_modules
    :rtype: List

    """
    subset_modules = []

    # Check if any of the required tests are specified in the list of modules found
    for required_module in module_subset:

        for test_module in test_modules:
            if required_module in test_module:
                subset_modules.append(test_module)
                continue

    return subset_modules


def execute_tests(dirs, results_dir, test_type="acceptance", clean_pool=False, modules=None, skip_modules=None):
    """
    Executes one or more tests for the specified test type

    :param test_type: Type of tests to be executed (acceptance)
    :type test_type: str
    :param dirs: Directories to check for matching test files
    :type dirs: list
    :param results_dir: Path to the directory where test results should be created
    :type results_dir: str
    :param clean_pool: Boolean indicating if the test pool should be torn down
    :type clean_pool: bool
    :param modules: Comma separated list of test modules
    :type modules: str
    :param skip_modules: Comma separated list of test modules to be skipped
    :type skip_modules: str

    :return: Return code (0 on success; 1 on test fail; 2 on test report generation fail)
    :rtype: int

    """

    # Needs to be run here as pexpect has a real big ego i.e. Only wants to be run in main process
    try:
        SHMLicense.install_license_script_dependencies()
    except Exception as e:
        log.logger.info("Failed to install SHM license dependencies on the system. Exception: {0}".format(str(e)))

    admin_user = get_workload_admin_user()

    start_time = datetime.datetime.now()

    # Clean pool if specified
    if test_type == "acceptance" or clean_pool:
        test_utils.clear_pool(test_type)

    # clear the test results directory
    _clear_test_results_dir(results_dir)
    # Make sure that the directory structure exists for Allure XML files
    allure_results_dir = os.path.join(results_dir, ALLURE_RESULTS_DIR)
    if not os.path.isdir(allure_results_dir):
        os.makedirs(allure_results_dir)

    global RESULTS_PATH
    RESULTS_PATH = results_dir

    # Get the list of test modules we want to execute
    test_modules = _get_acceptance_tests(dirs, modules=modules, skip_modules=skip_modules)

    # Initialize the node pool if not already done so
    if test_type == "acceptance":
        CHUNK_SIZE = 1
        log.logger.debug("Initializing node pool for acceptance tests")
        test_utils.init_pool("acceptance")
        shuffle_acceptance_tests(test_modules)


    # Run the tests (Note: This forks individual processes for each test)
    log.logger.info("Running {0} test processes in parallel...".format(test_type))
    if not test_modules:
        log.logger.error('No files found matching the given criteria')
        return 1

    # Check nodes are started, added and synced
    try:
        check_nodes(test_type, admin_user)
    except Exception as e:
        log.logger.error("Exception raised checking nodes: {0}".format(str(e)))
        return 1

    return_codes = _pool(_execute_test, test_modules, chunk_size=CHUNK_SIZE)

    # Copy the logs
    logs_dir = "{0}/bladerunners/jenkins/logs".format(STORAGE_DIR)
    if filesystem.does_dir_exist(logs_dir):
        destination_path = "/tmp/acc_logs/{0}".format(time.time())
        filesystem.copy(logs_dir, destination_path)

    # Figure out the overall result of the run by analyzing all of the module results
    test_result = False if any(return_codes) != 0 else True

    # Inject environment and version information into the report
    _update_environment_info(results_dir)

    # Build the final report
    log.logger.debug("Generating allure report after test run...")
    report_result = _generate_allure_report(results_dir)

    # Determine the overall return code
    if not test_result:
        rc = 1
        print "{0}FAIL: One or more tests failed or errored{1}\n".format(RED_TEXT, NORMAL_TEXT)
    elif not report_result:
        rc = 2
        print "{0}All tests passed, but an error was encountered while generating the test report{1}\n".format(RED_TEXT, NORMAL_TEXT)
    else:
        rc = 0
        print "{0}PASS: All tests passed and test report was generated successfully{1}\n".format(GREEN_TEXT, NORMAL_TEXT)

    # Print out the execution time
    elapsed_time = datetime.datetime.now() - start_time
    duration = "%.3fs" % float((elapsed_time.microseconds + (float(elapsed_time.seconds) + elapsed_time.days * 24 * 3600) * 10 ** 6) / 10 ** 6)
    print "TEST EXECUTION + REPORT GENERATION TIME: {0}{1}{2}\n".format(GREEN_TEXT, duration, NORMAL_TEXT)

    return rc


def execute_unit_tests(dirs, results_dir, profile_code=False, fast_unit_tests=False, show_time_taken_per_testcase=False,
                       nose_cover_packages=None, cover_min_percentage=70, modules=None):
    """
    Executes all unit test modules via nose

    :param dirs: directories which contain the unit tests
    :param results_dir: directory where to store the results under
    :param profile_code: Flag controlling whether modules will be profiled during unit test execution
    :type profile_code: boolean
    :param fast_unit_tests: Flag controlling whether unit tests should be run in parallel and without coverage to speed up execution
    :type fast_unit_tests: boolean
    :param show_time_taken_per_testcase: Flag controlling whether the execution times for the longest tests are shown or not
    :type show_time_taken_per_testcase: boolean
    :type nose_cover_packages: list
    :param nose_cover_packages: List of directories to be included in the coverage report
    :type cover_min_percentage: int
    :param cover_min_percentage: percentage of coverage required to pass the unit test execution
    :type modules: str
    :param modules: Comma separated list of test modules

    :return: Return code (0 on success; 1 on test fail)
    :rtype: int

    """

    print "\n************************"
    print "* EXECUTING UNIT TESTS *"
    print "************************"

    _clear_test_results_dir(results_dir)

    results_dir = os.path.join(results_dir, RESULTS_DIR)

    raw_stats_file_path = os.path.abspath(os.path.join(results_dir, ".profile.stats"))
    profile_report_file_path = os.path.abspath(os.path.join(results_dir, "unit-profile.stats"))
    output_dir = os.path.abspath(os.path.join(results_dir, "unit-coverage-report"))
    start_page = os.path.abspath(os.path.join(results_dir, "unit-coverage-report", "index.html"))
    test_modules = None

    if show_time_taken_per_testcase:
        timer_options = "--with-timer --timer-ok={0} --timer-warning={0} --timer-filter warning,error".format(TIMER_OK_LIMIT)
    else:
        timer_options = ""

    if profile_code:
        cmd = PROFILED_UNIT_TEST_CMD
    elif fast_unit_tests:
        cmd = FAST_UNIT_TEST_CMD
    elif modules:
        cmd = UNIT_SINGLE_TEST_CMD
        cover_min_percentage = 1
        test_modules = ",".join(_get_acceptance_tests(dirs, modules=modules, unit=True))
    else:
        cmd = UNIT_TEST_CMD

    if nose_cover_packages is None:
        nose_cover_packages = ['enmutils.lib', 'enmutils_int.lib']

    cmd = cmd.format(dirs=' '.join(dirs), packages=','.join(nose_cover_packages),
                     stats_file=raw_stats_file_path, cover_min_percentage=cover_min_percentage,
                     cover_config_path=COVERAGE_RC_FILE, modules=test_modules, timer_options=timer_options)

    print "Executing unit tests... "
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

    # Grab stdout line by line as it becomes available
    while process.poll() is None:
        try:
            line = process.stdout.readline().strip()
            if len(line) > 0:
                print line
        except:
            pass

    # There may be some final output still available after the process has exited, print that
    print process.stdout.read()

    # Generate basic profiling data for the run
    if profile_code:
        output_stream = StringIO.StringIO()
        stats = pstats.Stats(raw_stats_file_path, stream=output_stream)
        stats.sort_stats('cumtime')
        stats.print_stats("/enmutils*/lib/")

        with open(profile_report_file_path, 'w') as handle:
            handle.write(output_stream.getvalue())

        output_stream.close()

    rc = process.returncode

    if rc != 0:
        print "\n\n{0}FAIL: Fails and/or errors detected in unit test results (see output above for more information){1}\n".format(RED_TEXT, NORMAL_TEXT)
        rc = 1
    else:
        _, coverage_stdout = _execute_command(COVERAGE_CMD.format(html_dir=output_dir, accept_tests=None))
        print coverage_stdout

    if not fast_unit_tests and os.path.exists(start_page):
        print "\nUnit coverage report can be found at {0}{1}{2}\n".format(PURPLE_TEXT, start_page, NORMAL_TEXT)

    if profile_code and os.path.exists(profile_report_file_path):
        print "Profile statistics from unit test run can be found at {0}{1}{2}\n".format(PURPLE_TEXT, profile_report_file_path, NORMAL_TEXT)

    return rc


def display_allure_report(results_dir):
    """
    Serves out the Allure test report from the localhost

    :return: Return code (0 on success; 1 on fail)
    :rtype: int

    """

    ip_address = None
    rc = 1

    # Build the absolute paths
    extract_allure_commandline_archive()
    jar_path = os.path.abspath(ALLURE_BAT)
    report_path = os.path.abspath(os.path.join(results_dir, RESULTS_DIR, "report"))

    # Get the IP address of the local host
    (rc, ip_address) = _execute_command("hostname -I | awk '{ print $1 }'")
    if rc == 0:
        ip_address = ip_address.strip()
    else:
        print("\nERROR: Could not determine primary IP address for local host")

    if ip_address is not None:
        cmd = SERVE_ALLURE_REPORT_CMD.format(jar_path, report_path)

        # Kick off the process
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        # Grab stdout line by line as it becomes available
        while process.poll() is None:
            try:
                line = process.stdout.readline().strip()
                if len(line) > 0 and "Open report [http://localhost" in line:
                    line = line.replace("Open report ", "")
                    line = line.replace("localhost", ip_address).replace("[", "").replace("]", "")
                    print("\nOpen this URL to view the Allure test report remotely in browser: {0}{1}{2}\n"
                          .format(PURPLE_TEXT, line, NORMAL_TEXT))
                    print("You may need to temporaily disable the firewall on the MS to view the report")
                    print("Hit {0}ctrl-c{1} when you are finished viewing the report to stop serving the report\n"
                          .format(YELLOW_TEXT, NORMAL_TEXT))
            except:
                pass

        # When the subprocess terminates there might be unconsumed output, so grab any remaining output
        rc = 0

    return rc


def check_nodes(test_type, admin_user):

    nodes = test_utils.get_pool(test_type).allocate_nodes(UnavailableNodes())
    log.logger.debug("There are {0} nodes in the acceptance pool.".format(len(nodes)))

    nodes_not_started = netsim_executor.check_nodes_started(nodes)
    if nodes_not_started:
        try:
            PowerNodes(nodes_not_started).start()
        except Exception as e:
            log.logger.debug("Exception while running start nodes command: {0}".format(str(e)))
        nodes_not_started = netsim_executor.check_nodes_started(nodes)

    nodes_not_created = TestFixture.verify_nodes_exist(admin_user, nodes, get_all=True)
    nodes_not_synced = TestFixture.verify_nodes_are_synced(admin_user, nodes)

    if nodes_not_started:
        log.logger.debug("Nodes not started: {0}".format(",".join([node.node_id for node in nodes_not_started])))
    if nodes_not_created:
        log.logger.debug("Nodes not created: {0}".format(",".join([node.node_id for node in nodes_not_created])))
    if nodes_not_synced:
        log.logger.debug("Nodes not synced : {0}".format(",".join([node.node_id for node in nodes_not_synced])))

    unavailable_nodes = nodes_not_created.union(nodes_not_synced)
    test_utils.get_pool("acceptance").return_nodes(set(nodes) - set(unavailable_nodes))

    log.logger.debug("Number of nodes available for tests: {0}".format(len(nodes) - len(unavailable_nodes)))


def object_diff(git_repo):
    rc = 0
    modules_found = []

    try:
        modified, renamed, deleted = categorise_staged_files(git_repo)
    except:
        modified = {}
        renamed = []
        deleted = []

    files_to_check = FILES_TO_CHECK.split(",")
    for module in files_to_check:
        if modified.has_key(module):
            modules_found.append(module)

    if modules_found or renamed or deleted:
        print "\n"
        print "**************************************"
        print "*     CHECKING FOR UPGRADE ISSUES    *"
        print "**************************************"
        print "\n"

        if modules_found:
            print "You have modified some critical modules. Have you... "
            print "(1) added or removed any attributes from classes in these modules"
            print "(2) added or removed classes from a module"
            print "    which could lead to a break after upgrading Utilities RPM?"
            print ""
            for m in modules_found:
                print "    {0}{1}{2}".format(GREEN_TEXT, m, NORMAL_TEXT)
            print ""

        if renamed:
            print "You have renamed or moved the following modules in library folders. It may lead to broken references after upgrading Utilities RPM "
            print ""
            for r in renamed:
                print "    {0}{1}{2}".format(GREEN_TEXT, r, NORMAL_TEXT)
            print ""

        if deleted:
            print "You have deleted the following modules in library folders. Check that deleting these files will not lead to any broken references after upgrade"
            print ""
            for d in deleted:
                print "    {0}{1}{2}".format(GREEN_TEXT, d, NORMAL_TEXT)

            print ""
        print "If your changes won't break Utilities tools after RPM upgrade then please type 'y' to commit (type 'n' to quit)"

        sys.stdin = open('/dev/tty')
        while True:
            choice = raw_input('> ')

            if choice == 'y':
                break
            elif choice == 'n':
                rc = 1
                break
            else:
                print "You typed {0}. Please type 'y' or 'n'".format(choice)

    return rc


def categorise_staged_files(git_repo_dir):
    """
    Sort the the staged files into modification types

    :param git_repo_dir: path to the git repository root
    :rtype: dict

    """

    (rc, stdout) = _execute_command("cd {0}; git diff --cached --find-renames --name-status".format(os.path.abspath(git_repo_dir)))
    if rc:
        raise RuntimeError("Could not get list of modified files ({rc}): {error}".format(rc=rc, error=stdout))

    modified = {}
    renamed = []
    deleted = []
    for line in stdout.strip().splitlines():
        data = line.split()
        if len(data) < 2:
            continue

        modification_type = data[0]
        file_path = data[1]

        if file_path.endswith(".py") and not any(f in file_path for f in IGNORED_FILES):

            split_path = file_path.split("/")
            module_name = split_path[-1]

            if "M" in modification_type:
                modified[module_name] = file_path
                continue

            if COMMON_LIB in file_path or INTERNAL_LIB in file_path:
                if "R" in modification_type:
                    renamed.append(module_name)
                elif "D" in modification_type:
                    deleted.append(module_name)

    return modified, renamed, deleted


class UnavailableNodes(object):
    NUM_NODES = {}
    NODE_VERSION = None

    def __init__(self):
        self.__name__ = "UnavailableNodes"


def shuffle_acceptance_tests(test_modules):
    """
    Create pseudorandom test order for acceptance tests. This will ensure longer tests are started first.
    :param test_modules: List of acceptance test modules
    :type test_modules: list
    """
    long_tests = ['a_tests_cm_import.py', 'a_tests_pm_subscriptions.py']
    random.shuffle(test_modules)

    for i, module in enumerate(test_modules):
        for test in long_tests:
            if test in module:
                test_modules.insert(0, test_modules.pop(i))


def check_missing_keys():
    """
    This test compares all profile entries in all network files to the forty_network file.
    Profiles can be excluded via the exceptions list.
    """
    log.logger.info("\n{0}\n* CHECKING FOR NETWORK KEY VIOLATIONS *\n{0}\n".format(TESTER_OUTPUT_DIVS))
    difference_list = []
    excluded_keys = ["NODE_FILTER"]
    exceptions_list = ["NHM_SETUP", "CELLMGT_08"]
    for app in networks.get("forty_k_network"):
        for profile, values in networks.get("forty_k_network").get(app).items():
            if profile in exceptions_list:
                continue
            forty_profile_keys = remove_basic_keys(set(values.keys()), app, profile)
            forty_profile_keys = forty_profile_keys.difference(excluded_keys)
            difference_list.extend(check_keys(app, profile, forty_profile_keys, excluded_keys))

    log.logger.warn("The following profiles were ignored during key check:{0}".format(exceptions_list))
    log.logger.warn("The following optional keys were ignored :{0}".format(excluded_keys))
    log.logger.warn("If these profiles/keys were changed, check manually.")
    return not difference_list


def check_keys(app, profile, forty_profile_keys, excluded_keys):
    """
    Performs the key comparisons basic on the keys provided
    :param excluded_keys: Keys that are optional, thus excluded
    :type excluded_keys: list
    :param forty_profile_keys: Keys from the forty network
    :type forty_profile_keys: set
    :param app: The application that is to be checked
    :type app: str
    :param profile: The profile that is to be checked
    ::type profile: str
    :return: The list of the differences in keys, if any
    :rtype: list
    """
    difference_list = []
    all_networks = deepcopy(networks)
    del all_networks['forty_k_network']
    del all_networks['basic']
    for network, applications in all_networks.items():
        if applications[app].get(profile):
            net_keys = set(applications[app].get(profile).keys())
            net_keys = net_keys.difference(excluded_keys)
            if not forty_profile_keys == net_keys:
                difference_string = ''
                difference_string += "Your config keys are different: {0}:{1}\n".format(network, profile)
                difference_string += "40: {}\n".format(sorted(forty_profile_keys))
                difference_string += "  : {}\n".format(sorted(net_keys))

                if forty_profile_keys.difference(net_keys):
                    difference_string += "Missing keys: {}\n".format(
                        forty_profile_keys.difference(net_keys))
                if net_keys.difference(forty_profile_keys):
                    difference_string += "Additional Keys: {}\n\n".format(
                        net_keys.difference(forty_profile_keys))
                log.logger.warn(difference_string)
                difference_list.append(difference_string)

    return difference_list


def check_staged_files_for_sleep_function(files_to_check):
    """
    Function to check if the staged files have any of the sleep functions of profile.py in the changes

    :param files_to_check: List of the staged files to be checked
    :type files_to_check: list

    :return: Boolean indicating if the function(s) are present
    :rtype: bool
    """
    log.logger.info("\n{0}\n* CHECKING FOR SCHEDULING KEY VIOLATIONS *\n{0}\n".format(TESTER_OUTPUT_DIVS))
    sleep_funcs = ['self.sleep_until_next_scheduled_iteration',
                   'self.sleep', 'self.sleep_until_time', 'self.sleep_until_day']
    for file_to_check in files_to_check:
        updated_lines = fetch_diff_from_staged_files(file_to_check)
        for line in updated_lines:
            if any([_ for _ in sleep_funcs if _ == line.split('+')[-1].strip().split('(')[0]]):
                return True


def fetch_profiles_from_staged_files(files_to_check):
    """
    Function to determine if the basic network file has been updated and return any updated profiles

    :param files_to_check: List of the staged files to be checked
    :type files_to_check: list

    :return: List of updated profiles if any
    :rtype: list
    """
    for file_to_check in files_to_check:
        if file_to_check.endswith('basic_network.py'):
            updated_lines = fetch_diff_from_staged_files(file_to_check)
            return fetch_updated_profiles(updated_lines)
    return []


def fetch_updated_profiles(output):
    """
    Parse the supplied git diff output for any updated profiles

    :param output: List of updated strings fetched from git diff
    :type output: list

    :return: List of any updated profiles
    :rtype: list
    """
    updated_profiles = []
    for line in output:
        if 'UPDATE' in line:
            updated_profiles.append(line.split(":")[0].split("'")[1].strip())
    return updated_profiles


def fetch_diff_from_staged_files(file_to_check):
    """
    Fetch the git diff of the supplied file

    :param file_to_check: File path to get the git diff
    :type file_to_check: str

    :return: List of the updated lines in the file supplied
    :rtype: list
    """
    updated_lines = []
    rc, output = commands.getstatusoutput("git diff HEAD~ {0}".format(file_to_check))
    if not rc:
        for line in output.split("\n"):
            if line.startswith("+ "):
                updated_lines.append(line)
    return updated_lines


def check_sleep_attribute_available(files_to_check):
    """
    Check any updated profiles have updated or added sleep functionality without correct keys

    :param files_to_check: List of the staged files
    :type files_to_check: list
    """
    profile_names = fetch_profiles_from_staged_files(files_to_check)
    all_networks = deepcopy(networks)
    missing_keys = {}
    del all_networks['basic']
    for profile_name in profile_names:
        for network in all_networks.keys():
            network_key = network
            for app in all_networks.get(network).keys():
                if (profile_name in all_networks.get(network).get(app).keys() and
                        not any([time_key for time_key in TIME_KEYS if time_key in all_networks.get(
                            network).get(app).get(profile_name).keys()])):
                    missing_keys[network_key] = profile_name
    if missing_keys:
        log.logger.warn("Possible key(s) missing: {0} from {1}".format(TIME_KEYS, missing_keys))


def remove_basic_keys(forty_profile_keys, app, profile):
    """
    Removes basic keys from forty key
    :param forty_profile_keys: Keys from the forty network
    :type forty_profile_keys: set
    :param app: The application that need is to be checked
    :type app: str
    :param profile: The profile that is to be checked
    ::type profile: str
    :return: Forty network profile keys without the basic keys
    :rtype: set
    """
    basic_keys = set(networks.get("basic").get(app).get(profile))
    for key in basic_keys:
        if key in forty_profile_keys:
            forty_profile_keys.remove(key)
    return forty_profile_keys


def validate_open_api_specification():
    """
    Validate Openapi specification files.
    :return: Test passed
    :rtype: bool
    """

    errors = []
    log.logger.info("\n{0}\n* CHECKING FORMAT OF OPENAPI SPECIFICATIONS *\n{0}\n".format(TESTER_OUTPUT_DIVS))

    for file_name in os.listdir(OPENAPI_DIR):
        service_name = file_name.split('.yml')[0]
        try:
            get_url_view_function_map(service_name)
        except InvalidOpenapiFormat as e:
            errors.append(e)
    if errors:
        log.logger.warn('\n'.join([str(error) for error in errors]))
        return False
    return True


def extract_allure_commandline_archive():
    """
    Extract the allure archive if needed.
    """
    cmd = "tar xvf {0} -C {1}".format(ALLURE_ARCHIVE, ALLURE_DIR)
    if not filesystem.does_dir_exist(ALLURE_DIR):
        filesystem.create_dir(ALLURE_DIR)
        shell.run_local_cmd(cmd)
    elif not filesystem.does_file_exist(os.path.join(ALLURE_DIR, "bin", "allure")):
        shell.run_local_cmd(cmd)
