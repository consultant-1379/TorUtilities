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

from enmutils_int.bin.configure_wlvm import DEPLOYMENT_NAME_EXAMPLE as DEPLOYMENT


commands = (
    # Command            Expected return codes       Expected strings in stdout
    # #########################################################################

    # CLEANUP: (PRE-TESTS)
    # Clean up prior to running any tests if required
    ('/bin/echo "INTERNAL - CONFIGURE WLVM TOOL TEST"', [], []),
    # Ensure puppet service is not running, as otherwise, it will reinstall ERICddc & ERICddccore packages on VAPP MS
    ('service puppet stop', [], []),
    # Ensure esmon service is running, as it's required to simulate EMP in cloud
    ('service esmon start', [], []),
    # Wait for 60s to allow esmon to fully startup so that ssh to VM is possible later on
    ('service esmon start', [], []),

    # Remove DDC package from server via rpm tool
    ('/bin/rpm -e ERICddc_CXP9030294', [], []),
    ('rpm -qa | egrep ERICddc_CXP9030294', [1], []),
    # Remove DDCcore package from server via rpm tool
    ('/bin/rpm -e ERICddccore_CXP9035927', [], []),
    ('rpm -qa | egrep ERICddccore_CXP9035927', [1], []),
    # Remove DDC directory from server to ensure clean base
    ('rm -rf /var/tmp/ddc_data;', [], []),

    # #########################################################################

    # TESTS 4 configure_wlvm
    # Tests Description:
    #       Verify that configure_wlvm works as expected
    #
    # CASE 1: configure_wlvm
    #
    # scenario: test invalid arguments
    ('configure_wlvm {0}'.format(DEPLOYMENT), [2], ['validation has failed']),
    ('configure_wlvm {} --check_all_packages'.format(DEPLOYMENT), [2], ['validation has failed']),
    # scenario: test help message
    ('configure_wlvm -h', [0], ['Usage:', 'Options:', '{}'.format(DEPLOYMENT)]),
    # scenarios: run different options
    ('configure_wlvm {} --check_packages'.format(DEPLOYMENT), [0], ['All required packages installed']),

    ('configure_wlvm {} --configure_ntp'.format(DEPLOYMENT), [0], ['NTP Configuration complete']),
    # need to disrupt NTP for next test
    ('service ntpd restart', [], []),
    ('configure_wlvm {} --configure_ntp'.format(DEPLOYMENT), [0], ['NTP Configuration complete']),

    ('configure_wlvm {} --set_enm_locations'.format(DEPLOYMENT), [0], ['EMP added', 'ENM_URL added']),

    ('configure_wlvm {} --fetch_private_key'.format(DEPLOYMENT), [0], ['private key has been written',
                                                                       'Correct permissions set']),

    # Revert certain settings to the ones applicable for this vapp instead of the DEPLOYMENT after last 2 tests so that
    # the next test will work as expected
    ('/bin/sed -i "s/export ENM_URL=.*/export ENM_URL=enmapache.athtem.eei.ericsson.se/" /root/.bashrc', [], []),

    # Using esmon VM to simulate emp VM in order to make VAPP act like a Cloud ENM deployment
    ('ssh -i /var/tmp/enm_keypair.pem cloud-user@$EMP sudo consul members|grep esmon', [0], ['alive']),
    # Test ssh access to emp
    ('ssh -q -i /var/tmp/enm_keypair.pem -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null '
     'cloud-user@$EMP date', [0], []),

    ('configure_wlvm {} --store_private_key_on_emp'.format(DEPLOYMENT), [0], ['File successfully copied to EMP']),

    # Verify that both ERICddc & ERICddccore packages are still not installed
    ('rpm -qa | egrep ERICddc_CXP9030294', [1], []),
    ('rpm -qa | egrep ERICddccore_CXP9035927', [1], []),

    # Install DDCcore package via configure_wlvm
    ('configure_wlvm {} --install_ddc'.format(DEPLOYMENT), [0], ['Package is installed']),
    ('configure_wlvm {} --install_ddc'.format(DEPLOYMENT), [0], ['DDC Core package already installed']),
    ('rpm -qa | egrep ERICddc_CXP9030294', [1], []),
    ('rpm -qa | egrep ERICddccore_CXP9035927', [0], []),

    # Remove DDCcore package via rpm tool
    ('/bin/rpm -e ERICddccore_CXP9035927', [0], []),
    ('rpm -qa | egrep ERICddccore_CXP9035927', [1], []),

    # Verify DDC & DDBcore packages are not listed
    ('rpm -qa | egrep ddc', [1], []),

    # Fetch DDC package and Install DDC package onto server via rpm tool
    ('PACKAGE=ERICddc_CXP9030294; VERSION=$(ssh -i /var/tmp/enm_keypair.pem cloud-user@$EMP '
     '/usr/bin/repoquery --qf  %{version} $PACKAGE); '
     'SERVER="https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443"; '
     'URLPATH="/nexus/content/repositories/releases/com/ericsson/cifwk/diagmon"; '
     'wget -O /var/tmp/$PACKAGE-$VERSION.rpm $SERVER$URLPATH/$PACKAGE/$VERSION/$PACKAGE-$VERSION.rpm '
     '-e use_proxy=yes -e https_proxy=atproxy1.athtem.eei.ericsson.se:3128 2>&1;'
     '/bin/rpm -ivh /var/tmp/$PACKAGE-$VERSION.rpm --nodeps', [0], []),
    ('rpm -qa | egrep ERICddc_CXP9030294', [0], []),
    ('rpm -qa | egrep ERICddccore_CXP9035927', [1], []),

    # Ensure tool will install DDCcore package if DDC package is already installed
    ('configure_wlvm {} --install_ddc'.format(DEPLOYMENT), [0], ['Package is installed']),
    ('rpm -qa | egrep ERICddc_CXP9030294', [1], []),
    ('rpm -qa | egrep ERICddccore_CXP9035927', [0], []),

    ('configure_wlvm {} --configure_ddc_on_enm'.format(DEPLOYMENT), [0], ['WORKLOAD Entry added']),

    ('configure_wlvm {} --setup_ddc_collection_of_workload_files'.format(DEPLOYMENT), [0], [
        'DDC Plugin script file created', 'DDC Plugin dat file created']),
    ('configure_wlvm {} --get_wlvm_hostname_from_dit'.format(DEPLOYMENT), [0], ['wlvm']),

    # #########################################################################

    # CLEAN UP: (POST-TESTS)
    #

    # remove artifacts added above
    ('/bin/rm -f /var/ericsson/ddc_data/config/server.txt', [], []),
    # Stop esmon service to reduce CPU load on MS, after tests are complete
    ('/sbin/service esmon stop', [], []),
    ('for service in deploymentinfo node user profile; do /sbin/service ${service}manager restart; done', [], []),

)
