"""
This file is designed be run by batch_runner tool

batch_runner tool expects 'commands' tuple, to be structured as follows:

'commands': Is the 3 column tuple containing:
column 1: The actual command to be executed. Provide full paths when possible.
column 2: The list of expected return codes. If the actual turn code does not
       match this list of expected return codes, the command will fail.
       Leave list empty if you don't care about the return code.
column 3: The list of expected strings to be found in the response.stdout
       If the actual output of the command does not match this list of
       expected return codes, the command will fail.
       Leave this list empty if you don't care about command output.
"""
from enmutils_int.lib.helper_methods import list_netsim_simulations
from enmutils_int.lib.nexus import get_prev_sprint_relased_version as rpm_in_prev_sprint
from enmutils_int.lib.schedules.full_schedule import PLACEHOLDERS

CONCURRENT_RUN = False

# Select small simulation when possible with ERBS nodes
simulations = [sim for sim in list_netsim_simulations() if 'LTE' in sim and 'limx' in sim]
simulation = simulations[0] if (simulations and simulations[0]) else "LTEJ4555-limx10-1.8K-FDD-LTE03"
node_dir = 'workload_nodes'
num_nodes = 3
#
check_running_daemons_cmd = '/bin/ps -ef | /bin/grep -i .env/bin/daemon'
workload_status_cmd = 'workload status --test-only'
no_running_profiles_on_the_system_msg = 'No active profile(s) running on the system'
no_running_profiles_with_priority_msg = 'No active profile(s) running on the system of this priority'
no_running_profiles_with_priority_and_category_msg = 'No active profile(s) running on the system of categories/names provided with priority'
no_diff_information_msg = 'No \'diff\' information to display for the profiles provided'
profile_not_running_msg = 'profiles are currently not running:'
successfully_initiated_msg = 'Successfully initiated'
schedule_action_complete = 'complete.'
attempting_to_stop_msg = 'Attempting to stop:'
sleep_cmd = '/bin/sleep 10;'
rpm_check_installed_cmd = '/bin/rpm -qa | /bin/grep  ERICtorutilities'
#
test_rpm = rpm_in_prev_sprint()
# Example of placeholder profile. Lets test that it can not be started etc.
placeholder_profile = PLACEHOLDERS['PLACEHOLDERS'].keys()[0]
real_profile = 'SECUI_03'
priority_one_profile = 'SECUI_04'
NSSUTILS_TOOL_LOCATION = "/opt/ericsson/nssutils/bin/"

commands = (
    # Command            Expected return codes       Expected strings in stdout
    # #########################################################################
    #
    #
    # TESTS 4 workload tool
    # Tests Description:
    #       Verify that all workload commands work as expected
    #
    #
    # CLEANUP & SETUP
    # Clean up prior to running any tests if required
    #
    ('/bin/echo "INTERNAL - WORKLOAD TOOL TEST"', [], []),

    # Verify version of package installed
    (rpm_check_installed_cmd, [0], []),

    # Stop all profiles if they are running
    ('workload stop all', [0, 1], []),
    (sleep_cmd, [], []),
    ('{0}'.format(workload_status_cmd), [1], [no_running_profiles_on_the_system_msg]),
    # Check if there are profiles running on the system
    # Improve so that we eliminate profiles that we use
    ('/bin/echo "Running workload daemons:"; {0}'.format(check_running_daemons_cmd), [], []),
    # Setup simulations and prepare node pool
    ('network clear', [], []),
    ('{2}node_populator unmanage {0} 1-{1}'.format(node_dir, num_nodes, NSSUTILS_TOOL_LOCATION), [], []),
    ('{2}node_populator delete {0} 1-{1}'.format(node_dir, num_nodes, NSSUTILS_TOOL_LOCATION), [], []),
    ('workload remove all', [], []),
    ('workload list all', [], ['No nodes']),
    # Remove enmutils directories
    ('/bin/rm -rf /tmp/torutilities /tmp/enmutils {0}'.format(node_dir), [0], []),
    # Start simulation and setup network
    ('{1}netsim start netsim {0}'.format(simulation, NSSUTILS_TOOL_LOCATION), [0], []),
    ('{2}netsim fetch netsim {0} {1}'.format(simulation, node_dir, NSSUTILS_TOOL_LOCATION), [0], []),
    ('{1}node_populator parse {0} {0}'.format(node_dir, NSSUTILS_TOOL_LOCATION), [0], []),
    ('{2}node_populator create {0} 0-{1} --identity'.format(node_dir, num_nodes, NSSUTILS_TOOL_LOCATION), [], []),
    ('workload add {0}'.format(node_dir), [], []),
    ('workload list all', [], []),
    #
    # #########################################################################
    # CASE 0: workload sanity checks
    ('workload status', [1], ['No active profile', 'running']),
    ('workload start notexisting', [1], ['Invalid']),
    ('workload start {0} -x --force'.format(real_profile), [0], ['Successfully initiated']),
    ('/bin/sleep 5', [], []),
    ('workload stop {0}'.format(real_profile), [0], ['Successfully initiated']),

    # CASE 1: workload describe
    #
    # scenario: valid profile
    ('workload describe {0}'.format(real_profile.lower()), [0], ['Please refer to the latest ENM TERE']),
    # scenario: invalid profile
    ('workload describe doc_100', [1], ['Invalid', 'doc_100']),
    # scenario: valid profile but expecting wrong strings to be found
    ('workload describe {0}'.format(real_profile.lower()), [0], ['Description', 'of the profile: {0}'.format(real_profile)]),
    #
    # CASE 2: workload profiles
    #
    # scenario: test 'workload profiles' returns valid profiles names in CAPITAL letters
    ('workload profiles', [0], ['Existing Profiles', 'FMX_01', '{0}'.format(real_profile)]),
    # scenario: test 'workload profiles' returns not formatted profiles names
    #
    # CASE 3: workload category
    #
    # scenario: test 'workload category' returns valid categories
    ('workload category', [0], ['Categories:', 'fmx', 'doc', 'cmevents_nbi']),
    #
    # scenario: starting invalid category fails
    ('workload start not-existing-category -x --category', [1], ['Invalid Categories: not-existing-category']),
    ('workload stop not-existing-category --category', [1], ['Invalid Categories: not-existing-category']),
    #
    # scenario:  category valid and some profiles in category running & some not running
    ('workload start {0} -xN --test-only --force'.format('DOC_01,CMEVENTS_NBI_01'), [0], []),
    ('{0} DOC_01'.format(workload_status_cmd), [0], ['DOC_01', 'OK']),
    ('workload start doc -xN --test-only --category --force', [1], ['profiles were already started: [DOC_01]']),
    ('workload clear-errors', [0], []),
    ('{0} doc_01'.format(workload_status_cmd), [0], ['DOC_01', 'OK']),
    ('{0} cmevents_nbi_01'.format(workload_status_cmd), [], ['CMEVENTS_NBI_01', 'OK']),
    ('workload stop doc,cmevents_nbi --category --test-only -N', [0], []),
    ('{0} '.format(workload_status_cmd), [1], [no_running_profiles_on_the_system_msg]),
    #
    # scenario: category valid & duplicates are OK
    # but invalid category specified should return with rc=1
    ('workload start doc,cmevents_nbi -xN --category --force --test-only', [0], [successfully_initiated_msg, 'DOC_01', '']),
    ('{0} doc_01'.format(workload_status_cmd), [0], ['DOC_01', 'OK']),
    ('workload clear-errors', [0], []),
    ('workload clean-pid {0}'.format(real_profile), [0], ['Please be patient...']),
    ('{0} cmevents_nbi_01'.format(workload_status_cmd), [0], ['CMEVENTS_NBI_01', 'OK']),
    ('{0} --lastrun'.format(workload_status_cmd), [0], []),
    #
    # CASE 4: workload start
    #
    # scenario:  attempt to start started valid profiles
    ('workload start doc_01 -xN --test-only', [1], ['already started']),
    ('workload stop -N doc_01 --test-only', [0], []),
    ('{0} doc_01'.format(workload_status_cmd), [1], [profile_not_running_msg]),
    ('workload stop -N doc,cmevents_nbi --category --test-only', [0], []),
    ('{0} cmevents_nbi_01'.format(workload_status_cmd), [1], [profile_not_running_msg]),
    #
    # CASE 5: workload status
    #
    # scenario: no profiles are running. verify that the correct message is displayed
    ('{0}'.format(workload_status_cmd), [1], [no_running_profiles_on_the_system_msg]),
    #
    # scenario: display status of not running profile
    ('{0} doc_01'.format(workload_status_cmd), [1], [profile_not_running_msg]),
    ('{0} doc_01 --verbose'.format(workload_status_cmd), [1], [profile_not_running_msg]),
    ('{0} doc_01 --errors'.format(workload_status_cmd), [1], [profile_not_running_msg]),
    #
    # scenario: no profiles are running. verify that the correct message is displayed when given a priority
    ('{0} --priority=1'.format(workload_status_cmd), [1], [no_running_profiles_with_priority_msg]),
    ('{0} -c doc --priority=1'.format(workload_status_cmd), [1], [no_running_profiles_with_priority_and_category_msg]),
    #
    # scenario: test all when doc_01 running
    ('workload start doc_01 -xN --test-only --force', [0], [successfully_initiated_msg, 'DOC_01', ' watch/tail the logs to view']),
    ('{0}'.format(workload_status_cmd), [0], ['DOC_01', 'OK']),
    ('{0} doc_01 --errors'.format(workload_status_cmd), [0], []),
    ('{0} doc_01 --errors --total=2'.format(workload_status_cmd), [0], []),
    # 0 and any negative number will display all errors. Max number of errors is set to 5
    ('{0} doc_01 --errors --total=-2'.format(workload_status_cmd), [0], []),
    ('{0} doc_01 --errors -t 2'.format(workload_status_cmd), [0], []),
    ('{0} doc_01 --errors -t 20'.format(workload_status_cmd), [0], []),
    ('{0} doc_01 -v --error-type=PROFILE -t 20'.format(workload_status_cmd), [0], []),
    # given a priority
    ('{0} --priority=1'.format(workload_status_cmd), [1], [no_running_profiles_with_priority_msg]),
    # given a category and priority
    ('{0} -c doc --priority=1'.format(workload_status_cmd), [1], [no_running_profiles_with_priority_and_category_msg]),
    # stop doc_01
    ('workload stop -N doc_01 --test-only', [0], [attempting_to_stop_msg, 'DOC_01', successfully_initiated_msg, 'profile teardown']),
    ('{0}'.format(workload_status_cmd), [1], []),
    # 'No profiles to stop.' message is returned when profile not running
    ('workload stop -N doc --category --test-only', [1], ['No profiles to stop.']),
    ('{0} '.format(workload_status_cmd), [1], [no_running_profiles_on_the_system_msg]),
    #
    # scenario: MIX workload start & stop & category
    # category valid and all profiles in category - not running
    # verify that we can start all profiles within that category
    ('workload stop doc -N --test-only --category', [1], ['No profiles to stop']),
    ('{0} doc_01'.format(workload_status_cmd), [1], [profile_not_running_msg]),
    ('{0} cmevents_nbi_01'.format(workload_status_cmd), [1], [profile_not_running_msg]),
    ('workload start doc,cmevents_nbi -xN --test-only --category --force', [0], [successfully_initiated_msg]),
    ('workload clear-errors', [0], []),
    ('{0} doc_01'.format(workload_status_cmd), [0], ['DOC_01', 'OK']),
    ('{0} cmevents_nbi_01'.format(workload_status_cmd), [0], ['CMEVENTS_NBI_01', 'OK']),
    ('workload stop doc_01,cmevents_nbi_01 -N --test-only --category', [1], ['Invalid Categories: cmevents_nbi_01, doc_01']),
    #
    ('workload stop doc,cmevents_nbi -N --test-only --category', [0], []),
    ('{0}'.format(workload_status_cmd), [1], [no_running_profiles_on_the_system_msg]),
    #
    # CASE 8: workload diff
    #
    # verify diff cli:
    #   some positive cases
    ('workload diff', [0], ['Profile']),
    ('workload diff | cat -vet | egrep Profile.*Running | egrep 94m', [0], []),
    ('workload diff --no-ansi | cat -vet | egrep Profile.*Running | egrep 94m', [1], []),
    ('workload diff --rpm-version=latest', [0], ['Profile', 'Supported']),
    # priority
    ('workload diff --priority=1', [0], ['Profile', 'Running']),
    # priority and category
    ('workload diff -c fm --priority=2', [0], ['Profile', 'Running']),
    # priority and list of profile names
    ('workload diff {0} --priority=2'.format(real_profile), [1], [no_diff_information_msg]),
    ('workload diff --updated', [0], []),
    #   some negative cases
    ('workload diff doc_01, --priority=1', [1], ['Invalid profile names']),
    ('workload diff --rpm-version=bad_version ', [0, 1], ['Invalid version provided']),
    ('workload diff --rpm-version {0} --network-size=40k'.format(test_rpm), [0], []),
    ('workload diff --rpm-version {0} --network-type=cpp'.format(test_rpm), [2], []),
    ('workload diff --priority=3', [0], ['Invalid priority rating specified']),
    # CASE 10: workload test basic functionality with placeholders profiles
    #
    ('workload start {0} -xN'.format(placeholder_profile), [1],
     ['Skipping unsupported', placeholder_profile, 'The following profiles were not started:']),
    ('{0} {1}'.format(workload_status_cmd, placeholder_profile), [1], ['currently not running:', placeholder_profile]),
    #
    #
    # CASE 11: workload start unsupported profile with --force option
    #
    # we going to use placeholders profile as an example of unsupported profile
    ('workload start {0} -xN --force'.format(placeholder_profile), [0], ['Successfully initiated']),
    ('workload clear-errors', [0], []),
    ('{0} {1}'.format(workload_status_cmd, placeholder_profile), [0], [placeholder_profile]),
    ('workload stop {0} -N'.format(placeholder_profile), [0], ['Successfully initiated ', placeholder_profile]),
    ('{0} {1}'.format(workload_status_cmd, placeholder_profile), [1], ['currently not running', placeholder_profile]),
    #
    # CASE 13: workload restart
    #
    # scenario: test restart functionality
    # invalid parameters, no profiles provided
    ('workload restart -xN', [2], ['ERROR']),
    # test default restart
    ('{0}'.format(workload_status_cmd), [1], [no_running_profiles_on_the_system_msg]),
    ('workload start {0} -xN --force'.format(real_profile), [0], ['Successfully initiated']),
    ('workload restart {0} -xN --force'.format(real_profile), [0], ['Attempting to stop', real_profile]),
    ('{0} {1}'.format(workload_status_cmd, real_profile), [0], [real_profile, 'Name', 'State', 'Status']),
    ('workload stop {0} -N'.format(real_profile), [0], ['Successfully initiated']),
    #
    #
    ('network clear', [], []),
    ('{2}node_populator unmanage {0} 1-{1}'.format(node_dir, num_nodes, NSSUTILS_TOOL_LOCATION), [], []),
    ('{2}node_populator delete {0} 1-{1}'.format(node_dir, num_nodes, NSSUTILS_TOOL_LOCATION), [], []),
    ('workload remove all', [], []),
    ('workload list all', [], ['No nodes']),
)
