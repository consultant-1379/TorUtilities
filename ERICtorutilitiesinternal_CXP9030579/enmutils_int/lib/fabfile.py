# ********************************************************************
# Name    : FabFile
# Summary : Python Fabric functional module - http://www.fabfile.org/
#           Provides functionality for executing shell commands over
#           locally and remotely over SSH, used mainly for Jenkins
#           job, acceptance, KGB+N, workload restart.
# ********************************************************************

import os
import sys

from enmutils_int.lib.test_settings import UPDATE_NEXUS_URL_COMMAND
from fabric.api import env, run, prefix, local
from fabric.context_managers import cd, settings, hide
from fabric.contrib.files import exists, append, comment
from fabric.contrib.project import rsync_project
from fabric.operations import get, put
from unipath import Path

VENV_DIR_NAME = '.env'
ENMUTILS_PROJECT_TOOLS_DIR_NAME = 'TorUtilities_tools'
ENMUTILS_PROJECT_DIR_NAME = 'ERICtorutilities_CXP9030570'
ENMUTILS_INT_PROJECT_DIR_NAME = 'ERICtorutilitiesinternal_CXP9030579'
ENMUTILS_TESTSLIB_DIR_NAME = 'torutilities_testslib'
PROD_BIN_DIR = "/opt/ericsson/enmutils/bin/"
ACCEPTANCE_TEST_RUNNING_FLAG_FILE = "/tmp/acceptance_test_is_running_here"
STORAGE_DIR = "/home/enmutils"
NSSUTILS_TOOL_LOCATION = "/opt/ericsson/nssutils/bin/"
JENKINS_NODES = "/opt/ericsson/nssutils/etc/nodes/"


def copy_new(clean='False', jenkins='False', acceptance=False):
    """
    Usage: fab copy_new remote_dir:<name_of_dir>

    :type clean: string
    :param clean: Option to remove the target directory on the remote MS before copying
    :type jenkins: bool
    :param jenkins: Boolean to indicate if jenkins server used or not
    :type acceptance: bool
    :param acceptance: Boolean to indicate if acceptance tests are to be ran

    Either provide the host as a global env var in env.hosts in this
    module above or enter host on the command line as hosts:<host>. If
    host is not found, it will be prompted for on the command line.
    """

    if clean == "True":
        run("rm -rf {0}".format(env.project_root))

    run("mkdir -p {0}".format(env.project_root))

    local_project_path = Path(__file__).ancestor(4)
    if jenkins == "True":
        if acceptance:
            copy_zipped_project(local_project_path)
        else:
            put(local_path=local_project_path.child(ENMUTILS_PROJECT_DIR_NAME), remote_path=env.project_root,
                mirror_local_mode=True)
            put(local_path=local_project_path.child(ENMUTILS_INT_PROJECT_DIR_NAME), remote_path=env.project_root,
                mirror_local_mode=True)
            put(local_path=local_project_path.child(ENMUTILS_PROJECT_TOOLS_DIR_NAME), remote_path=env.project_root,
                mirror_local_mode=True)
            put(local_path=local_project_path.child(ENMUTILS_TESTSLIB_DIR_NAME), remote_path=env.project_root,
                mirror_local_mode=True)
    else:
        rsync_project(remote_dir=env.project_root, local_dir=os.path.join(local_project_path, ''), delete=False,
                      extra_opts='-ra',
                      exclude=("*.doc", "*.pyc", "*.idea", "*.git", "*.egg-info", "*.env", "test-results"))


def ensure_pip():
    """
    Ensure that pip is installed on the remote host
    """
    with settings(warn_only=True):
        result = run('which pip')
    if result.return_code != 0:
        run('easy_install --no-deps {0}'.format(env.internal_epp.child('pip-6.1.1-py2.7.egg')))


def ensure_virtualenv():
    """
    Ensure that virtualenv is installed on the remote host
    """

    ensure_pip()

    # If '.env' is already installed return
    if exists('{0}/bin'.format(env.venv)):
        return

    python27_path = '/opt/ericsson/enmutils/.env/bin/python2.7'

    # Defaults to centos 6.4 system python 2.6.6
    interpreter = '/usr/bin/python'

    run('pip install {0}'.format(env.internal_epp.child('virtualenv-1.11.6-py2.py3-none-any.whl')))

    # If production rpm is installed with python 2.7.x, use that interpreter
    if exists(python27_path):
        interpreter = python27_path

    # Change to project root directory and install virtualenv with the specified interpreter
    with cd(env.project_root):
        run("virtualenv --no-site-packages -p {0} {1}".format(interpreter, env.venv))


def change_local_prop(prop_name, prop_val):
    """
    Change the ENVIRON from 'local' to 'testing'  in the local properties file

    :type prop_name: string
    :param prop_name: The property name to look for in the file
    :type prop_val: string
    :param prop_val: The property value to replace with in the file
    """
    local_props_file = env.project_root.child(ENMUTILS_PROJECT_DIR_NAME, 'enmutils', 'local_properties.py')

    # Change to the parent root directory an
    with cd(env.project_root):
        prop_name = prop_name.upper()
        # Find 'ENVIRON' pattern in the local props file and comment the line away
        comment(local_props_file, r"^{0}\s*=".format(prop_name))
        prop_string = '{0}="{1}"'.format(prop_name, prop_val)
        # Add a new string pattern to the file
        append(local_props_file, prop_string)


def deploy(remote_dir, clean='False', jenkins='False', acceptance=False):
    """
    Copy the code to a remote server and enable virtualenv

    :type remote_dir: string
    :param remote_dir: The remote directory to deploy the code on
    :type clean: string
    :param clean: Option to remove the target directory on the remote MS before copying
    :type jenkins: string
    :param jenkins: Boolean to indicate if jenkins server used or not
    :type acceptance: bool
    :param acceptance: Boolean to indicate if acceptance tests are to be ran
    """

    # Get all the necessary paths on the remote host
    env.project_root = Path(remote_dir)
    env.venv = env.project_root.child(VENV_DIR_NAME)
    enmutils_path = env.project_root.child(ENMUTILS_PROJECT_DIR_NAME)
    enmutils_tools_path = env.project_root.child(ENMUTILS_PROJECT_TOOLS_DIR_NAME)
    enmutils_int_path = env.project_root.child(ENMUTILS_INT_PROJECT_DIR_NAME)
    enmutils_testslib_path = env.project_root.child(ENMUTILS_TESTSLIB_DIR_NAME)
    env.epp = enmutils_path.child('enmutils', '3pp')
    env.internal_epp = enmutils_int_path.child('enmutils_int', '3pp')

    # Copy the code
    copy_new(clean=clean, jenkins=jenkins, acceptance=acceptance)

    # Change the ENVIRON from 'local' to 'testing'  in the local properties file
    change_local_prop("ENVIRON", "testing")

    # Ensure that virtualenv is enabled and installed
    ensure_virtualenv()

    # We need to activate the virtualenv first in order to install production and internal packages.
    # Deactivate when done
    with prefix('source {0}/bin/activate'.format(env.venv)):
        with cd(env.project_root):
            # Later version of pip required for paramiko 2.4.2 and for some of it's dependencies
            run('pip install {0}'.format(env.internal_epp.child('pip-9.0.3-py2.py3-none-any.whl')))

            # Install the production lib package
            run('pip install --no-index --find-links={0} --ignore-installed --editable {1}'.format(env.epp,
                                                                                                   enmutils_path))

            # Install the production tools package
            run('pip install --no-index --find-links={0} --editable {1}'.format(env.epp, enmutils_tools_path))

            # Install the internal app
            run('pip install --no-index --find-links={0} --editable {1}[testing]'.format(env.internal_epp,
                                                                                         enmutils_int_path))

            run('pip install --no-index --find-links={0} --editable {1}'.format(enmutils_testslib_path.child('3pp'),
                                                                                enmutils_testslib_path))
            run('pip install --no-index --find-links={0} requests_toolbelt'.format(env.internal_epp))


def run_acceptance(remote_dir, clean='False', jenkins='False', number_of_backups_to_keep=10, skip_modules=""):
    """
    Copy the code to a remote server and enable virtualenv and run acceptance tests
    :type remote_dir: str
    :param remote_dir: The remote directory to deploy the code on
    :type clean: str
    :param clean: Option to remove the target directory on the remote MS before copying
    :type jenkins: str
    :param jenkins: Boolean to indicate if jenkins server used or not
    :param number_of_backups_to_keep: Number of backups to complete
    :type number_of_backups_to_keep: int
    :param skip_modules: Comma separated list of modules to skip
    :type skip_modules: str
    """
    run('echo $(date +%y%m%d.%H%M%S) > {0}'.format(ACCEPTANCE_TEST_RUNNING_FLAG_FILE))

    deploy(remote_dir=remote_dir, clean=clean, jenkins=jenkins, acceptance=True)

    # Activate the virtualenv and run acceptance job
    with prefix('source {0}/bin/activate'.format(env.venv)):
        with settings(warn_only=True):
            skip_option = " --skip={0}".format(skip_modules)
            result = run('tester acceptance --root_path={0}{1}'.format(remote_dir, skip_option))
            run('network netsync &')

    get_acceptance_test_results(remote_dir)

    backup_logs_from_current_run(remote_dir, number_of_backups_to_keep=number_of_backups_to_keep)

    stop_acceptance(result.return_code)


def check_if_acceptance_tests_are_running():
    """
    Checks for existence of flag file to determine if acceptance jobs are running or not
    """
    return_code = 1 if exists(ACCEPTANCE_TEST_RUNNING_FLAG_FILE) else 0
    sys.exit(return_code)


def remove_persisted_key(key, index="0", force="false"):
    """
    Runs the persistence tool out of production directory to clear the specified key

    :type key: string
    :param key: The key in persistence to remove
    :type index: string
    :param index: Optional argument to remove the key from a specific persistence index
    :type force: string
    :param force: Optional argument to remove the key using force flag
    """

    if force == "false":
        run(os.path.join(PROD_BIN_DIR, "persistence") + ' remove ' + key + " --index=" + index)
    else:
        run(os.path.join(PROD_BIN_DIR, "persistence") + ' remove ' + key + " --index=" + index + " force")


def delete_persisted_node_list(node_file_path=None):
    """
    Runs the node populator tool out of production directory to delete the specified list of nodes

    :type node_file_path: string
    :param node_file_path: The absolute path to the list of nodes in persistence to delete,
    :return: Integer to indicate return code
    :rtype: int
    """
    with prefix('source {0}/bin/activate'.format(env.venv)):
        if not node_file_path:
            run(('{1}node_populator delete {0}/bladerunners/jenkins/ERICtorutilitiesinternal_CXP9030579/enmutils_int/'
                 'tests/etc/network_nodes/acceptance_list'.format(STORAGE_DIR, NSSUTILS_TOOL_LOCATION)))
        else:
            run('{0}node_populator delete {1}'.format(NSSUTILS_TOOL_LOCATION, node_file_path))
    return 0


def get_remote_files(remote_path, local_path):
    """
    Get files from remote server
    :type remote_path: string
    :param remote_path: Absolute path to directory or file on remote server
    :type local_path: string
    :param local_path: Path where files should be stored locally
    example:
        fab -f 'ERICtorutilitiesinternal_CXP9030579/enmutils_int/lib/fabfile.py' -H  root@$remote_hostname
        get_remote_files:remote_path='/home/enmutils/bladerunners/jenkins/logs',local_path='.'"""
    get(remote_path=remote_path, local_path=local_path)


def acceptance_test_setup(remote_dir, clean='False', jenkins='False', simulations=None, start=False, fetch=False,
                          nssutils_version="1.8.3"):
    """
    Runs the netsim tool  directory to start the specified simulations

    :type remote_dir: string
    :param remote_dir: Absolute path to directory or file on remote server
    :type simulations: str
    :param simulations: Optional string of simulations i.e. "LTE01;LTE02"
    :type start: bool
    :param start: True if we want to start the simulations
    :type fetch: bool
    :param fetch: True if we want to fetch and parse the acceptance simulations
    :type jenkins: str
    :param jenkins: Boolean to indicate if jenkins server used or not
    :type clean: string
    :param clean: Option to remove the target directory on the remote MS before copying
    :type nssutils_version: str
    :param nssutils_version: The version of NSSUtils to be installed.
    """
    simulations = simulations or []
    deploy(remote_dir=remote_dir, clean=clean, jenkins=jenkins)
    parsed_nodes_dir = "/var/enmutils/acceptance_list"
    with prefix('source {0}/bin/activate'.format(env.venv)):
        default_simulations = build_default_simulations_dictionary(nssutils_version=nssutils_version)
        sims = default_simulations.keys() if not simulations else simulations.split(";")

        with settings(warn_only=True):
            _disable_puppet_services_on_ms()
            _disable_esmon_service_on_ms()
            _increase_db_size()
            _delete_stats_file()
            netsim_start_str = '{1}netsim start netsim {0}'
            if start:
                run('{1}netsim restart netsim {0}'.format(
                    ",".join([sim for sim in sims if 'dg2' in sim.lower()]), NSSUTILS_TOOL_LOCATION))
                result = run(netsim_start_str.format(",".join(sims), NSSUTILS_TOOL_LOCATION))
                if result.return_code != 0:
                    _copy_netsim_id_and_restart_netsim(",".join(sims))
            dir_not_exists = run('ls {0}'.format(parsed_nodes_dir))
            if dir_not_exists:
                run("mkdir -p /var/enmutils ; touch /var/enmutils/acceptance_list")
                if fetch:
                    netsync_results = fetch_and_parse_sims(sims, default_simulations, parsed_nodes_dir)
                    if not netsync_results:
                        # Restarts cmserv, kpiserv and pmserv
                        run('/opt/ericsson/enminst/bin/vcs.bsh --restart -g Grp_CS_svc_cluster_cmserv,'
                            'Grp_CS_svc_cluster_kpiserv,Grp_CS_svc_cluster_pmserv')
                        # Model deployment SVC offlining but not onlining when done in builk
                        run('/opt/ericsson/enminst/bin/vcs.bsh --restart -g '
                            'Grp_CS_db_cluster_modeldeployment_clustered_service')
                        run('{0}network netsync'.format(PROD_BIN_DIR))
                        run(netsim_start_str.format(",".join(sims), NSSUTILS_TOOL_LOCATION))

    sys.exit(result.return_code)


def install_nssutils_rpm(rpm_version="1.7.4"):
    """
    Install the NSSUtils rpm on the remote deployment

    :param rpm_version: The version of NSSUtils to be installed.
    :type rpm_version: str
    """
    nssutils_rpm_location = ("https://arm901-eiffel004.athtem.eei.ericsson.se:8443/nexus/content/groups/enm_deploy_"
                             "proxy/com/ericsson/oss/services/nss/nssutils/ERICTWnssutils_CXP9036352/{0}/"
                             "ERICTWnssutils_CXP9036352-{0}.rpm")
    nssutils_rpm = "ERICTWnssutils_CXP9036352-{0}.rpm"
    with settings(warn_only=True):
        run("echo Fetching nssutils rpm version: [{0}] from nexus.".format(rpm_version))
        run("wget {0}".format(nssutils_rpm_location.format(rpm_version)))
        run("echo Installing nssutils rpm version: [{0}] from nexus.".format(rpm_version))
        run("yum install -y {0}".format(nssutils_rpm.format(rpm_version)))
        run("echo Installed nssutils rpm version: [{0}] from nexus.".format(rpm_version))
        with prefix('source {0}/bin/activate'.format(env.venv)):
            run('update_enmutils_rpm -l')


def fetch_and_parse_sims(sims, default_simulations, parsed_nodes_dir):
    """
    Fetch and parse sims

    :param sims: List of simulations
    :type sims: list
    :param default_simulations: Dictionary of default simulations
    :type default_simulations: dict
    :param parsed_nodes_dir: Directory where parsed nodes file is stored
    :type parsed_nodes_dir: str
    :return: Indication if node sync was successful (0 = success)
    :rtype: int
    """
    netsync_results = 0
    for index, sim in enumerate(sims):
        _fetch_and_parse_nodes(sim)
        if index == 0:
            run('sed -n 1,1p {0}{1} > {2}'.format(JENKINS_NODES, sims[0], parsed_nodes_dir))
        start = end = 0
        if len(default_simulations.get(sim)) > 1:
            start, end = default_simulations.get(sim)[0], default_simulations.get(sim)[1]
        _create_nodes_and_write_acceptance_list(sim, range_start=start, range_end=end)
        result = run('{0}network netsync'.format(PROD_BIN_DIR))
        netsync_results += result.return_code
    return netsync_results


def list_netsim_simulations():
    """
    Retrieve the list of netsim simulations

    :return: List of simulations found
    :rtype: list
    """
    with prefix('source {0}/bin/activate'.format(env.venv)):
        result = run('{0}netsim list netsim --no-ansi'.format(NSSUTILS_TOOL_LOCATION))
        return [sim.strip() for sim in result.split("\n")[3:]]


def build_default_simulations_dictionary(nssutils_version, max_retries=0):
    """
    Build a dictionary of the available simulations for use in the acceptance test pool


    :param nssutils_version: The version of NSSUtils to be installed.
    :type nssutils_version: str
    :param max_retries: Maximum number of retries in the case of an IndexError occurring
    :type max_retries: int

    :return: Dictionary of the available simulations for use in the acceptance test pool
    :rtype: dict
    """
    if not max_retries:
        install_nssutils_rpm(rpm_version=nssutils_version)
    with prefix('source {0}/bin/activate'.format(env.venv)):
        all_sims = list_netsim_simulations()
        simulation_dictionary = dict()
        try:
            simulation_dictionary[[sim for sim in all_sims if 'SGSN' in sim and 'UPGIND' not in sim][0]] = [1, 1]
            simulation_dictionary[[sim for sim in all_sims if 'MGw' in sim and 'UPGIND' not in sim][0]] = [1, 1]
            simulation_dictionary[[sim for sim in all_sims if 'RNC' in sim and "x4" in sim and 'UPGIND' not in
                                   sim][0]] = [1, 5]
            erbs_simulations = [sim for sim in all_sims if 'LTE' in sim and 'limx40' in sim and 'dg2' not in
                                sim.lower() and "LTEJ450" in sim][:2]
            radio_nodes = [sim for sim in all_sims if 'LTE' in sim and 'x40' in sim and 'dg2' in sim.lower()][:1]
            erbs_simulations.extend(radio_nodes)

            if not all([erbs_simulations, radio_nodes]):
                sys.exit(5)
            for erbs in erbs_simulations:
                simulation_dictionary[erbs] = [1, 40]
            return simulation_dictionary
        except IndexError:
            if max_retries < 3:
                max_retries += 1
                build_default_simulations_dictionary(nssutils_version, max_retries)


def _fetch_and_parse_nodes(sim):
    """
    Fetch and parse the provided simulation
    :type sim: str
    :param sim: Name of the simulation to be fetched and parse

    """
    fetched_nodes_dir = "/tmp/{0}".format(sim)
    result = run('{2}netsim fetch netsim {0} {1} --delete-files'.format(sim, fetched_nodes_dir, NSSUTILS_TOOL_LOCATION))
    if result.return_code != 0:
        _copy_netsim_id_and_restart_netsim(sim)
        run('{2}netsim fetch netsim {0} {1} --delete-files'.format(sim, fetched_nodes_dir, NSSUTILS_TOOL_LOCATION))
    result = run('{2}node_populator parse {0} {1}'.format(sim, fetched_nodes_dir, NSSUTILS_TOOL_LOCATION))
    if result.return_code != 0:
        run('/opt/ericsson/enminst/bin/vcs.bsh --restart -g Grp_CS_svc_cluster_cmserv')
        run('{2}node_populator parse {0} {1}'.format(sim, fetched_nodes_dir, NSSUTILS_TOOL_LOCATION))


def _create_nodes_and_write_acceptance_list(sim, range_start=0, range_end=0):
    """
    Create node(s) on enm and, write the created nodes, to the acceptance list

    :type sim: str
    :param sim: Name of the simulation to perform the  creation upon
    :type range_start: int
    :param range_start: Index of the node, to execute the create function from
    :type range_end: int
    :param range_end: Index of the node, to execute the create function to

    """
    parsed_nodes_dir = "/var/enmutils/acceptance_list"
    if range_start or range_end:
        run(('{3}node_populator create {0} {1}-{2}'.format(sim, range_start, range_end, NSSUTILS_TOOL_LOCATION)))
        run('sed -n {0},{1}p {2} >> {3}'.format(range_start + 1, range_end + 1, "{0}{1}".format(JENKINS_NODES, sim),
                                                parsed_nodes_dir))
    else:
        run(('{1}node_populator create {0}'.format(sim, NSSUTILS_TOOL_LOCATION)))
        run('cat {0} >> {1}'.format("{0}/{1}".format(JENKINS_NODES, sim), parsed_nodes_dir))


def _copy_netsim_id_and_restart_netsim(sims):
    """
    Method to copy the netsim ssh key, restart the netsim, and start the simulations provided

    :param sims: str, Simulation or comma separated list of simulations to start
    :type sims: str

    """
    with settings(prompts={'Password: ': 'netsim'}):
        run('ssh-copy-id netsim@netsim')
    run('ssh netsim@netsim \'inst/restart_netsim\'')
    run('{1}netsim start netsim {0}'.format(sims, NSSUTILS_TOOL_LOCATION))


def _delete_stats_file():
    """
    Replace PM DG2 stats file

    """
    with settings(prompts={'Password: ': 'netsim'}):
        run('ssh -o StrictHostKeyChecking=no netsim@netsim "touch old_pm_cron new_cron; crontab  -l > '
            'old_pm_cron; crontab new_cron"')


def _increase_db_size():
    """
    Increase the db volume

    """
    cmd = ("su - versant -c '/ericsson/versant/bin/addvol -n mydatavol1 -p /ericsson/versant_data/databases/"
           "dps_integration/mydatavol_file1 -s 2G dps_integration'")
    db = "db-1"
    script_cmd = ("{0}/bladerunners/jenkins/ERICtorutilitiesinternal_CXP9030579/enmutils_int/external_sources/"
                  "scripts/ssh_to_vm_and_su_root.exp {1} \"{2}\"".format(STORAGE_DIR, db, cmd))
    run(script_cmd)


def _disable_esmon_service_on_ms():
    """
    Disable the esmon service on the MS to recover server CPU and memory resources for other ENM processes

    """
    run("/sbin/service esmon stop")


def _disable_puppet_services_on_ms():
    """
    Disable the puppet services on the MS to recover server CPU and memory resources for other ENM processes.

    """
    run("/sbin/service puppet stop")
    run("/sbin/service puppetdb stop")


def run_kgb_tests(remote_dir, test_rpm_version="--latest", cmds_to_run="production.py", iterations=1, clean='False',
                  jenkins='False', nssutils_version="1.8.3"):
    """
    Executes the batch runner/KGB tests

    :type remote_dir: str
    :param remote_dir: Absolute path to directory or file on remote server
    :type test_rpm_version: str
    :param test_rpm_version: Package version
    :type cmds_to_run: str
    :param cmds_to_run: Which batch-runner test to run
    :type iterations: int
    :param iterations: Number of iterations to perform
    :type clean: str
    :param clean: Override the existing directory
    :type jenkins: str
    :param jenkins: Use the default jenkins directory
    :type nssutils_version: str
    :param nssutils_version: The version of NSSUtils to be installed.
    """
    deploy(remote_dir=os.path.join(remote_dir), clean=clean, jenkins=jenkins)
    install_nssutils_rpm(rpm_version=nssutils_version)
    with settings(warn_only=True):
        # Disabling some non-essential CPU-intensive resources on Vapp to prevent KGB+N tests from failing
        _disable_puppet_services_on_ms()
        run('service usermanager stop')
        run('service nodemanager stop')
        with prefix('source {0}/bin/activate'.format(env.venv)):
            local('echo Removing internal package before updating to latest.')
            run("{0}".format(UPDATE_NEXUS_URL_COMMAND))
            run("{0}".format(UPDATE_NEXUS_URL_COMMAND))
            run('update_enmutils_rpm {0}'.format(test_rpm_version))
        result = run(
            '/opt/ericsson/enmutils/bin/batch_runner '
            '/opt/ericsson/enmutils/.env/lib/python2.7/site-packages/enmutils_int/etc/batch/commands/{cmds_to_run} '
            '{iterations} --kgb={kgb}'.format(cmds_to_run=cmds_to_run, iterations=iterations, kgb=True))

    sys.exit(result.return_code)


def upgrade_rpm_and_restart_profiles(start_all, stop_all, restart_all, restart_all_updated, priority_one, priority_two,
                                     **kwargs):
    """
    Upgrade the installed rpm and perform the requested actions

    :param start_all: Start all profiles
    :type start_all: bool
    :param stop_all: Stop all profiles
    :type stop_all: bool
    :param restart_all: Restart all profiles
    :type restart_all: bool
    :param restart_all_updated: Restart all updated profiles only
    :type restart_all_updated: bool
    :param priority_one: Boolean flag to indicate the use of --priority=1 option
    :type priority_one: bool
    :param priority_two:Boolean flag to indicate the use of --priority=2 option
    :type priority_two: bool
    :param kwargs: Dictionary containing keyword arguments
    :type kwargs: dict
    """
    update_rpm_options = kwargs.pop('update_rpm_options', "")
    cbrs_setup = kwargs.pop('cbrs_setup', "false")
    ignore = kwargs.pop('ignore', None)
    if isinstance(ignore, str):
        ignore = ignore.split(",")
    elif ignore:
        local("echo Ignore profiles must be comma separated list, no profiles will be ignored.")
    base_commands = build_commands_list(True if start_all == "true" else False, True if stop_all == "true" else False,
                                        True if restart_all == "true" else False,
                                        True if restart_all_updated == "true" else False, ignore)
    commands = update_commands_with_priority_option(base_commands, True if priority_one == "true" else False,
                                                    True if priority_two == "true" else False)
    run("{0}".format(UPDATE_NEXUS_URL_COMMAND))
    result = run("/opt/ericsson/enmutils/.deploy/update_enmutils_rpm -l {0}".format(update_rpm_options))
    if result.return_code != 0:
        sys.exit(result.return_code)
    # Needs to be left to warn_only as "No profiles to start is treated like an error"
    with settings(warn_only=True):
        return_codes = []
        rc = 0
        for command in commands:
            result = run(command)
            if "No profiles to" in result.stdout:
                result.return_code = 0
            return_codes.append(result.return_code)
        if any(return_codes):
            rc = 1
        if cbrs_setup and cbrs_setup == "true":
            manage_cbrs_setup_profile()
    sys.exit(rc)


def manage_cbrs_setup_profile():
    """
    Check if CBRS Setup profile needs to be started or if restarted if updated.
    """
    result = run("pgrep -f 'CBRS_SETUP cbrs_setup'")
    if not result.return_code:
        result = run("/opt/ericsson/enmutils/bin/workload diff --updated --no-ansi | /bin/egrep CBRS_SETUP")
        if not result.return_code:
            run("/opt/ericsson/enmutils/bin/workload restart -xN cbrs_setup --force")
    else:
        run("/opt/ericsson/enmutils/bin/workload start -xN cbrs_setup --force")


def build_commands_list(start_all, stop_all, restart_all, restart_all_updated, ignore=None):
    """
    Build the basic list of commands

    :param start_all: Start all profiles
    :type start_all: bool
    :param stop_all: Stop all profiles
    :type stop_all: bool
    :param restart_all: Restart all profiles
    :type restart_all: bool
    :param restart_all_updated: Restart all updated profiles only
    :type restart_all_updated: bool
    :param ignore:List of profiles to ignore
    :type ignore:list

    :return: List of base commands to execute
    :rtype: list
    """

    cmd_root = "/opt/ericsson/enmutils/bin/workload {0} --jenkins"
    commands = []
    ignore_stub = " --ignore \"{0}\"".format(",".join(ignore)) if ignore else ""

    if stop_all:
        commands.append(cmd_root.format("stop all --force-stop"))
    if start_all:
        commands.append(cmd_root.format("start all{0}".format(ignore_stub)))
    if restart_all:
        commands.append(cmd_root.format("restart all --force-stop {0}".format(ignore_stub)))
    if restart_all_updated:
        commands.append(cmd_root.format("restart all --force-stop --updated{0}".format(ignore_stub)))
    return commands


def update_commands_with_priority_option(commands, priority_one=False, priority_two=False):
    """
    Update the list of commands to use the priority option
    :param commands: List of base commands to execute
    :type commands: list
    :param priority_one: Boolean flag to indicate the use of --priority=1 option
    :type priority_one: bool
    :param priority_two:Boolean flag to indicate the use of --priority=2 option
    :type priority_two: bool
    :return: List of updated base commands to execute
    :rtype: list
    """
    p1_stub = " --priority=1"
    p2_stub = " --priority=2"
    priority_one_list = ["{0}{1}".format(command, p1_stub) for command in commands]
    priority_two_list = ["{0}{1}".format(command, p2_stub) for command in commands]
    if not priority_two and not priority_one:
        return commands
    if not priority_two:
        return priority_one_list
    if not priority_one:
        return priority_two_list
    else:
        priority_one_list.extend(priority_two_list)
        local("echo updated commands list with priority option, updated commands: {0}".format(priority_one_list))
        return priority_one_list


def zip_file(archive_path, target_files, target_files_dir, run_local=True):
    """
    Zips the given list of target files into an archive.
    :param archive_path: absolute path archive to be created.
    :type archive_path: str
    :param target_files: list of file names to zip
    :type target_files: list
    :param target_files_dir: absolute path to directory where the target files are located.
    :type target_files_dir: str
    :param run_local: Run the command locally or remotely
    :type run_local: bool
    """
    with settings(hide("running"), warn_only=True):
        local("echo 'Zipping the following files: {0} at {1} to {2}'".format(' '.join(target_files), target_files_dir,
                                                                             archive_path))
        if run_local:
            result = local("tar -czf {0} -C {1} {2}".format(archive_path, target_files_dir, ' '.join(target_files)))
        else:
            with cd(target_files_dir):
                result = run('tar -czf {0} {1}'.format(archive_path, ' '.join(target_files)))
        local("echo 'Zipping files complete'")

    validate_result(result)


def unzip_file(target_archive, unzip_path='.', run_local=True):
    """
    Unzips the given target archive. Providing a unzip path will unzip the contents to that path
    :param target_archive: Name of the target archive to unzip
    :type target_archive: str
    :param unzip_path: Path to unzip the archive. Current working directroy by default
    :type unzip_path: str
    :param run_local: Run the command locally or remotely
    :type run_local: bool
    """

    with settings(hide('running'), warn_only=True):
        local("echo 'Unzipping {0} to {1}'".format(target_archive, unzip_path))
        if run_local:
            result = local('tar -xf {0} -C {1}'.format(target_archive, unzip_path))
        else:
            with cd(unzip_path):
                result = run('tar -xf {0}'.format(target_archive))
        local("echo 'Unzipping complete'")
    validate_result(result)


def copy_zipped_project(local_project_path):
    """
    Copy project files in compressed format and unzip.
    :param local_project_path: Path to local project files
    :type local_project_path: str
    """
    # Zip all project files before transfer to vApp
    target_files = [ENMUTILS_PROJECT_DIR_NAME, ENMUTILS_INT_PROJECT_DIR_NAME, ENMUTILS_PROJECT_TOOLS_DIR_NAME,
                    ENMUTILS_TESTSLIB_DIR_NAME]
    zip_file(os.path.join(local_project_path, 'project.tar.gz'), target_files, local_project_path)
    with hide("running"):
        run("echo Uploading file project.tar.gz")
        put(os.path.join(local_project_path, 'project.tar.gz'), remote_path=env.project_root)
        run("echo Upload complete")
    unzip_file('project.tar.gz', unzip_path=env.project_root, run_local=False)


def get_acceptance_test_results(remote_dir):
    """
    Download acceptance test results from remote dir.
    :param remote_dir: Path to test results
    :type remote_dir: str
    """
    out_path = '.'  # Current path on jenkins build directory
    remote_test_results_path = os.path.join(remote_dir, 'test-results')
    remote_archive_path = os.path.join(remote_dir, 'archive.tar.gz')

    zip_file(remote_archive_path, ["report", "allure-results"], remote_test_results_path, run_local=False)

    with hide('running'):
        local("echo 'Downloading zipped test results'")
        get(remote_path=remote_archive_path, local_path=out_path)
        local("echo 'Download complete'")
    unzip_file(os.path.join(out_path, 'archive.tar.gz'))


def backup_logs_from_current_run(remote_dir, number_of_backups_to_keep):
    """
    Make a backup of logs from current acceptance test run so that they are not immediately wiped once the next job runs
    :param remote_dir: Path to test results
    :type remote_dir: str
    :param number_of_backups_to_keep: Number of backups to complete
    :type number_of_backups_to_keep: int
    """
    time_of_test = run("/bin/cat {0}".format(ACCEPTANCE_TEST_RUNNING_FLAG_FILE)).split()[0]

    remote_enmutils_path = os.path.join(remote_dir, ENMUTILS_PROJECT_DIR_NAME)
    remote_backups_dir_path = os.path.join("/root", "bladerunners", "log_backups_from_previous_acceptance_test_runs")
    remote_archive_path = os.path.join(remote_backups_dir_path, "logs.{0}.tar.gz".format(time_of_test))

    run("mkdir -p {0}".format(remote_backups_dir_path))

    local("echo 'Removing any log backups older than recent {0} backups'".format(number_of_backups_to_keep))
    output = run("ls -tl {0} | egrep gz | awk '{{print $NF}}'".format(remote_backups_dir_path), warn_only=True)
    files = output.split()
    for index, filename in enumerate(files):
        if index + 1 > int(number_of_backups_to_keep):
            local("echo 'Removing backup file {0}/{1}'".format(remote_backups_dir_path, filename))
            run("rm -f {0}/{1}".format(remote_backups_dir_path, filename))

    path_to_torutils_service_logfiles = "/home/enmutils/services"
    path_to_torutils_main_logfiles = os.path.join(remote_enmutils_path, "logs")
    path_to_test_results = os.path.join(remote_dir, "test-results")

    local("echo 'Copying the Torutils service logs dir ({0}) to the Torutils main logs dir ({1})'"
          .format(path_to_torutils_service_logfiles, path_to_torutils_main_logfiles))
    run("/bin/cp -rp {0} {1}".format(path_to_torutils_service_logfiles, path_to_torutils_main_logfiles))

    local("echo 'Copying the test-results dir ({0}) to the Torutils main logs dir ({1})'"
          .format(path_to_torutils_service_logfiles, path_to_torutils_main_logfiles))
    run("/bin/cp -rp {0} {1}".format(path_to_test_results, path_to_torutils_main_logfiles))

    zip_file(remote_archive_path, ["logs"], remote_enmutils_path, run_local=False)
    local("echo 'Backup of logs complete'")


def stop_acceptance(return_code):
    """
    Stop acceptance tests
    :param return_code: Command return code
    :type return_code: int
    """
    if exists(ACCEPTANCE_TEST_RUNNING_FLAG_FILE):
        run('rm -f {0}'.format(ACCEPTANCE_TEST_RUNNING_FLAG_FILE))
    sys.exit(return_code)


def validate_result(result):
    """
    Validate the result. Stop acceptance test if non zero
    :param result: command result
    :type result: 'fabric.operations._AttributeString'
    """
    if result.return_code:
        stop_acceptance(result.return_code)
