"""
This file is designed be run by batch_runner tool

batch_runner tool expects 'commands' tuple, to be structured as follows:

'commands': Is the 3 column tuple containing:
column 1: the actual command to be executed. Provide full paths when possible
column 2: the list of expected return codes. If the actual turn code does not
       match this list of expected return codes, the command will fail.
       Leave list empty if you don't care about the return code
column 3: the list of expected strings to be found in the response.stdout
       If the actual output of the command does not match this list of
       expected return codes, the command will fail.
       Leave this list empty if you don't care about command output.
"""

from enmutils_int.lib.nexus import get_prev_sprint_relased_version as rpm_in_prev_sprint
from enmutils_int.bin.update_enmutils_rpm import _get_installed_version_of_package as get_installed_version
from enmutils_int.lib.test_settings import UPDATE_NEXUS_URL_COMMAND

rpm_check_installed_cmd = '/bin/rpm -qa | /bin/grep  ERICtorutilities'
prod_rpm = 'ERICtorutilities_CXP9030570'
int_rpm = 'ERICtorutilitiesinternal_CXP9030579'
int_tools = ['batch_runner', 'network', 'netsim', 'user_mgr', 'workload']
prod_tools = ['persistence', 'cli_app']
rpm_check_files_delivered_by_rpm = '/bin/rpm -ql {0}'
rpm_check_for_tools_files = '/bin/rpm -ql {0} | /bin/grep bin | /bin/egrep {1}'
test_rpm = rpm_in_prev_sprint()
existing_rpm_version = get_installed_version('prod')

commands = (
    # Command            Expected return codes       Expected strings in stdout
    # #########################################################################

    # CLEANUP
    # Clean up prior to running any tests if required
    ('/bin/echo "INTERNAL - UPGRADE ENMUTILS RPM TOOL TEST"', [], []),

    # sometimes seen: this error:  ' Thread died in Berkeley DB library' after execution of the below
    # keep watching this!
    # workaround:
    #    reboot LMS. Check with: 'rpm -qa | grep torutil' what is installed at present
    ('/usr/bin/yum clean all', [0], []),
    (rpm_check_installed_cmd, [], []),
    # Download and install ERICtorutilitiesinternal_CXP9030579 rpm if not installed that is of the same version as the
    # installed production package
    ('''
    if ! /bin/rpm -qa | /bin/grep -qw ERICtorutilitiesinternal_CXP9030579; then
    nexus=https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443/nexus
    gr=com.ericsson.dms.torutility
    art=ERICtorutilitiesinternal_CXP9030579
    ver=`/bin/rpm -q --qf "%{version}" ERICtorutilities_CXP9030570`
    # download from nexus
    /usr/bin/wget -qO /tmp/$art-$ver.rpm "$nexus/service/local/artifact/maven/redirect?r=releases&g=${gr}&a=${art}&v=${ver}&e=rpm"
    /usr/bin/yum localinstall -y /tmp/ERICtorutilitiesinternal_CXP9030579-$ver*.rpm
    fi;
    ''', [0], []),
    # remove downloaded rpm
    ('/bin/rm -rf /tmp/ERICtorutilitiesinternal_CXP9030579-$ver*.rpm', [0], []),
    # update  rpms to latest available
    ("{0}".format(UPDATE_NEXUS_URL_COMMAND), [], []),
    ('update_enmutils_rpm -l --prod-and-int-only', [], []),
    (rpm_check_installed_cmd, [], []),


    # #########################################################################

    # TESTS 4 update_enmutils_rpm
    # Tests Description:
    #       Verify that update_enmutils_rpm works as expected
    #
    # CASE 1: update_enmutils_rpm
    #
    # scenario: test invalid arguments
    ('update_enmutils_rpm version_number', [2], ['validation has failed']),
    ('update_enmutils_rpm 666.999.999.545', [2], ['Could not find version number 666.999.999.545', 'in Nexus']),
    ('update_enmutils_rpm 666.999.999.bad_version', [2], ['ENM Utilities RPM packages aren\'t available '
                                                          'for versions older than 4.13.1']),
    ('update_enmutils_rpm 1.2.3.4 extra_arg', [2], ['validation has failed']),
    # scenario: test help message
    ('update_enmutils_rpm -h', [0], ['Usage:', 'Arguments:', 'Examples:']),
    # scenario: test status command
    ('update_enmutils_rpm -s', [0], ['locally available', 'installed', 'latest available on Nexus']),
    # Test downgrade
    # Production package from the ENM iso, is stored in /var/www/html/ENM_ms/ directory
    # next command supposed to bring all rpms back to the version that come with ENM iso
    ("{0}".format(UPDATE_NEXUS_URL_COMMAND), [], []),
    ('PACKAGE=ERICtorutilities_CXP9030570;VERSION=$(ssh -i /var/tmp/enm_keypair.pem cloud-user@$EMP '
     '/usr/bin/repoquery --qf  %{version} $PACKAGE);update_enmutils_rpm $VERSION', [0], []),
    (rpm_check_installed_cmd, [0], []),
    ("{0}".format(UPDATE_NEXUS_URL_COMMAND), [], []),
    ('update_enmutils_rpm -s', [0], ['locally available', 'installed', 'latest available on Nexus']),
    # Test instalation/upgrade rpms to latest version available on Nexus
    ("{0}".format(UPDATE_NEXUS_URL_COMMAND), [], []),
    ('update_enmutils_rpm -l', [0], ['Upgrading prod', 'Upgrading int']),
    # scenario: install the internal and production rpms particular version
    ("{0}".format(UPDATE_NEXUS_URL_COMMAND), [], []),
    ('update_enmutils_rpm {0} --prod-and-int-only'.format(test_rpm), [0], ['installed successfully']),
    (rpm_check_installed_cmd, [0], []),
    ("{0}".format(UPDATE_NEXUS_URL_COMMAND), [], []),
    ('update_enmutils_rpm -s', [0], ['locally available', 'installed: {0}'.format(test_rpm), 'latest '
                                                                                             'available on Nexus']),
    # Test instalation/upgrade rpms to latest version available on Nexus
    ("{0}".format(UPDATE_NEXUS_URL_COMMAND), [], []),
    ('update_enmutils_rpm -l', [0], ['Upgrading prod', 'Upgrading int', 'installed successfully']),
    (rpm_check_installed_cmd, [0], []),
    ("{0}".format(UPDATE_NEXUS_URL_COMMAND), [], []),
    ('update_enmutils_rpm -s', [0], ['locally available', 'installed', 'latest available on Nexus']),
    # verify both rpms content. Each rpm should deliver all tool oriented files.
    # result of: TORF-124178
    (rpm_check_files_delivered_by_rpm.format(prod_rpm), [0], prod_tools),
    (rpm_check_files_delivered_by_rpm.format(int_rpm), [0], int_tools),
    # Check that internal tools files - not in production rpm
    # below gives: /bin/rpm -ql ERICtorutilities_CXP9030570 | /bin/grep bin |
    # /bin/egrep 'batch_runner|network|netsim|user_mgr|workload'
    (rpm_check_for_tools_files.format(prod_rpm, "'" + '|'.join(int_tools)) + "'", [1], []),
    # below gives: /bin/rpm -ql ERICtorutilitiesinternal_CXP9030579 | /bin/grep bin|
    # /bin/egrep 'persistence|cli_app'
    (rpm_check_for_tools_files.format(int_rpm, "'" + '|'.join(prod_tools)) + "'", [1], []),

    # #########################################################################

    # CLEAN UP: Ensure that we put the rpm version back to the same version as we got it
    #
    ("{0}".format(UPDATE_NEXUS_URL_COMMAND), [], []),
    ('update_enmutils_rpm {0}'.format(existing_rpm_version), [], []),
    (rpm_check_installed_cmd, [0], []),

)
