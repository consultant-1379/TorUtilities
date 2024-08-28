"""
This file is designed be run by batch_runner tool

batch_runner tool expects 'commands' tuple, to be structured as follows:

'commands': Is the 3 column tuple containing:
column 1: the actual command to be executed. Provide full paths when possible
column 2: the list of expected return codes. If the actual turn code does not
       match this list of expected return codes, the command will fail.
       Leave list empty if you don't care about the return code.
column 3: the list of expected strings to be found in the response.stdout
       If the actual output of the command does not match this list of
       expected return codes, the command will fail.
       Leave this list empty if you don't care about command output.
"""

from enmutils_int.lib import load_mgr
from enmutils_int.lib.helper_methods import list_netsim_simulations
from enmutils_int.lib.test_settings import UPDATE_NEXUS_URL_COMMAND

CONCURRENT_RUN = False

node_dir = 'workload_nodes'
num_nodes = 3
real_profile = 'AP_11'
NSSUTILS_TOOL_LOCATION = "/opt/ericsson/nssutils/bin/"
tool_location = "/opt/ericsson/enmutils/bin/"
workload_tool = "{0}workload".format(tool_location)
simulations = [sim for sim in list_netsim_simulations() if 'LTE' in sim and 'limx40' in sim]
simulation = simulations[0] if simulations[0] else "LTEJ4555-limx10-1.8K-FDD-LTE03"

# Messages
no_running_profiles_on_the_system_msg = 'No active profile(s) running on the system'
profile_not_running_msg = 'profiles are currently not running:'
specific_profile_not_running_msg = 'The following profiles are currently not running: [\'{}\']'


# Commands
sleep_cmd = '/bin/sleep 10;'
rpm_check_installed_cmd = '/bin/rpm -qa | /bin/grep  ERICtorutilities'
check_running_daemons_cmd = '/bin/ps -ef | /bin/grep -i .env/bin/daemon'
workload_status_cmd = '{0} status --test-only'.format(workload_tool)

# RPM versions required
latest_rpm_version, previous_rpm_version = load_mgr.get_comparative_versions()
commands = (
    # Command            Expected return codes       Expected strings in stdout
    # #########################################################################
    #
    #
    # TESTS Upgrade Test
    # Tests Description:
    #       Verify that workload status works as expected after upgrading from the previous sprints version
    #
    #
    # CLEANUP & SETUP
    # Clean up prior to running any tests if required
    #
    ('/bin/echo "PRODUCTION - DOWNGRADE + UPGRADE RPM TEST"', [], []),
    # Upgrade to the latest so we can perform our setup
    ("{0}".format(UPDATE_NEXUS_URL_COMMAND), [], []),
    ('update_enmutils_rpm -l', [0], []),
    # create adhoc schedule for template profiles
    # ('/bin/echo "from collections import OrderedDict\nNON_EXCLUSIVE = OrderedDict()\nnon_exclusive = NON_EXCLUSIVE[\''
    #  'DOC\'] = OrderedDict()\nnon_exclusive[\'DOC_01\'] = (0,0)\nnon_exclusive[\'CMEVENTS_NBI_01\']= (0,0) \nWORKLOAD = [NON_EXCLUSIVE]" > {0}'.format(test_schedule), [0], []),
    # Stop all profiles if they are running
    ('{} stop all -N --test-only'.format(workload_tool), [0, 1], []),
    ('{0} stop all -N --test-only'.format(workload_tool), [], []),
    (sleep_cmd, [], []),
    ('{0}'.format(workload_status_cmd), [1], [no_running_profiles_on_the_system_msg]),
    # Clear persistence
    ('{0}persistence clear force --auto-confirm'.format(tool_location), [0], []),
    # setup simulations and prepare node pool
    ('{0}network clear'.format(tool_location), [], []),
    ('{0} remove all'.format(workload_tool), [], []),
    ('{0} list all'.format(workload_tool), [], ['No nodes']),
    # remove enmutils directories
    ('/bin/rm -rf /tmp/torutilities /tmp/enmutils {0}'.format(node_dir), [0], []),
    # start simulation
    ('{1}netsim start netsim {0}'.format(simulation, NSSUTILS_TOOL_LOCATION), [0], []),
    # #########################################################################
    # CASE: UPGRADE. Run update_enmutils_rpm with running profiles
    #
    # scenario: test workload in upgrade scenario (from rpm released in the prev sprint to the latest) with profiles running
    #
    # # DOWNGRADE internal and production rpms to version: "test_rpm"
    ("{0}".format(UPDATE_NEXUS_URL_COMMAND), [], []),
    ('update_enmutils_rpm {0} --prod-and-int-only'.format(previous_rpm_version), [0], ['installed successfully']),
    (rpm_check_installed_cmd, [0], []),
    ("{0}".format(UPDATE_NEXUS_URL_COMMAND), [], []),
    ('update_enmutils_rpm -s', [0], ['locally available', 'installed: {0}'.format(previous_rpm_version), 'latest available on Nexus']),
    # #
    # # prepare workload pool based on the version of "test_rpm"
    ('{0}netsim fetch netsim {1} {2}'.format(NSSUTILS_TOOL_LOCATION, simulation, node_dir), [0], []),
    ('{0}node_populator parse {1} {1}'.format(NSSUTILS_TOOL_LOCATION, node_dir), [0], []),
    ('{0}node_populator create {1} 1-{2} --identity'.format(NSSUTILS_TOOL_LOCATION, node_dir, num_nodes), [], []),
    ('{0} add {1}'.format(workload_tool, node_dir), [], []),
    ('{0} list all'.format(workload_tool), [], []),
    #
    # start template profiles
    ('{0} start -xN doc_01,cmevents_nbi_01 --force --test-only'.format(workload_tool), [0], []),
    ('{0} doc_01'.format(workload_status_cmd), [0], ['DOC_01', 'OK']),
    ('{0} cmevents_nbi_01'.format(workload_status_cmd), [0], ['CMEVENTS_NBI_01', 'OK']),
    #
    # start real profile
    ('{0} start {1} -xN --force'.format(workload_tool, real_profile), [0], ['Successfully initiated']),
    ('{0} {1}'.format(workload_status_cmd, real_profile), [0], [real_profile, 'OK']),
    #
    #
    #
    # UPGRADE rpms to version under test
    ("{0}".format(UPDATE_NEXUS_URL_COMMAND), [], []),
    ('update_enmutils_rpm {0}'.format(latest_rpm_version), [0], ['Upgrading prod', 'Upgrading int', 'installed successfully']),
    (rpm_check_installed_cmd, [0], []),
    ("{0}".format(UPDATE_NEXUS_URL_COMMAND), [], []),
    ('update_enmutils_rpm -s', [0], ['locally available', 'installed', 'latest available on Nexus']),
    ('{0}'.format(workload_status_cmd), [0], ['DOC_01', 'CMEVENTS_NBI_01', real_profile, 'OK']),
    ('{0}persistence list'.format(tool_location), [0], []),
    #
    # Restart profiles
    ('{0} stop doc_01,cmevents_nbi_01 -N --test-only'.format(workload_tool), [0], []),
    ('{0} cmevents_nbi_01'.format(workload_status_cmd), [1], [specific_profile_not_running_msg.format("CMEVENTS_NBI_01")]),
    ('{0} restart -xN cmevents_nbi_01 --test-only'.format(workload_tool), [1], ["No profiles to restart."]),
    ('{0} restart -xN all'.format(workload_tool), [0], []),
    (sleep_cmd, [], []),
    ('{0} ap_11'.format(workload_status_cmd), [0], ['AP_11', 'OK']),
    #
    #
    # Stop profiles
    ('{0} stop all -N'.format(workload_tool), [0], []),
    (sleep_cmd, [], []),
    ('{0} {1}'.format(workload_status_cmd, real_profile), [1], [profile_not_running_msg, real_profile]),
    #
    ('{0}'.format(workload_status_cmd), [1], [no_running_profiles_on_the_system_msg]),
    ('{0}persistence list'.format(tool_location), [0], []),
    ('{0} start {1} -xN --force'.format(workload_tool, real_profile), [0], ['Successfully initiated']),
    # DOWNGRADE rpms to version under test
    ("{0}".format(UPDATE_NEXUS_URL_COMMAND), [], []),
    ('update_enmutils_rpm {0}'.format(previous_rpm_version), [0], ['Downgrading prod', 'Downgrading int', 'installed successfully']),
    (rpm_check_installed_cmd, [0], []),
    ("{0}".format(UPDATE_NEXUS_URL_COMMAND), [], []),
    ('update_enmutils_rpm -s', [0], ['locally available', 'installed: {0}'.format(previous_rpm_version), 'latest available on Nexus']),
    ('{0}'.format(workload_status_cmd), [0], [real_profile, 'OK']),
    #
    # Stop profiles
    ('{0} stop all -N'.format(workload_tool), [0], []),
    (sleep_cmd, [], []),
    ('{0} {1}'.format(workload_status_cmd, real_profile), [1], [profile_not_running_msg, real_profile]),
    ('{0}'.format(workload_status_cmd), [1], [no_running_profiles_on_the_system_msg]),
    ('{0}network clear'.format(tool_location), [], []),
    ('{0} remove all'.format(workload_tool), [], []),
    ('{0} list all'.format(workload_tool), [], ['No nodes']),
    ("{0}".format(UPDATE_NEXUS_URL_COMMAND), [], []),
    ('update_enmutils_rpm {0}'.format(latest_rpm_version), [0], ['Upgrading prod', 'Upgrading int', 'installed successfully'])
)
