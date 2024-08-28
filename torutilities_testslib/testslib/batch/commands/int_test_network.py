# This is the file used by batch_runner
#
# batch runner expects 'commands' to be set in the following way:
#
# 'commands': Is the 3 column tuple containing:
# column 1: the actual command to be executed. Provide full paths when possible
# column 2: the list of expected return codes. If the actual turn code does not
#           match this list of expected return codes, the command will fail.
#           Leave list empty if you don't care about the return code
# column 3: the list of expected strings to be found in the response.stdout
#           If the actual output of the command does not match this list of
#           expected return codes, the command will fail.
#           Leave this list empty if you don't care about command output.
#

from enmutils_int.lib.helper_methods import list_netsim_simulations

CONCURRENT_RUN = False

lte_160_sims = [sim for sim in list_netsim_simulations() if 'LTE' in sim and 'limx40' in sim]

SIM = lte_160_sims[0] if lte_160_sims else 'ERROR: COULD NOT MATCH ANY SIMULATION'

SIM_NAME_PARTIAL = SIM.split('-')[-1]  # ex.: LTE05
NODE_REGEX = '*{0}*'.format(SIM_NAME_PARTIAL)
NODE = 'netsim_{0}ERBS00001'.format(SIM_NAME_PARTIAL)
NSSUTILS_TOOL_LOCATION = "/opt/ericsson/nssutils/bin/"

# make it dynamic
NODE_LIST = 'netsim_{0}ERBS00001,netsim_{0}ERBS00002,netsim_{0}ERBS00003'.format(SIM_NAME_PARTIAL)
ZERO_INSTANCES = "0 instance(s) found"

commands = (
    # Command            Expected return codes       Expected strings in stdout
    # #########################################################################

    # CLEANUP
    # Clean up prior to running any tests if required
    ('/bin/echo "INTERNAL - NETWORK TOOL TEST"', [], []),


    # #########################################################################

    # TESTS 4 network
    # Tests Description:
    #       Verify that network works as expected
    #
    # CASE 1: network generic
    #
    # scenario: valid arguments
    ('network -h', [0], []),
    # scenario: invalid arguments
    ('network', [2], ['Invalid command line arguments']),
    #
    # CASE 2: network info, netypes
    #
    ('{1}netsim fetch netsim {0} erbs'.format(SIM, NSSUTILS_TOOL_LOCATION), [0], []),
    ('{0}node_populator parse erbs erbs'.format(NSSUTILS_TOOL_LOCATION), [0], []),
    ('{0}node_populator delete erbs 1-3'.format(NSSUTILS_TOOL_LOCATION), [], []),
    ('{0}node_populator create erbs 1-3'.format(NSSUTILS_TOOL_LOCATION), [0], []),
    # scenario: valid arguments
    ('network info {0}'.format(NODE), [0], []),
    ('network netypes', [0], []),
    ('network netypes ERBS', [0], []),
    # scenario: invalid arguments
    ('network info LTENOTAREALNODE', [0], ['Node LTENOTAREALNODE does not exist on the system']),
    ('network netypes ANYTYPES', [0], ['NO ENM SUPPORTED MODEL INFO FOR NE TYPES']),
    ('network status --node LTENOTAREALNODE', [1], ['Could not get sync state for node LTENOTAREALNODE']),
    #
    # CASE 2: network status
    #
    ('network status', [0], []),
    ('network status --show-nodes', [0], []),
    ('network status --show-unsynced', [0], []),
    ('network status --groups', [0], []),
    ('network status --groups --show-nodes', [0], []),
    ('network status --groups --show-unsynced', [0], []),
    ('network status --groups fm', [0], []),
    ('network status --groups fm --show-nodes', [0], []),
    ('network status --groups fm --show-unsynced', [0], []),
    ('network status --groups fm,cm,pm', [0], []),
    ('network sync-list {0}'.format(NODE_LIST), [0, 1], []),
    ('network status --node {0}'.format(NODE), [0], []),
    # scenario: invalid arguments
    ('network status --node LTENOTAREALNODE', [1], ['Could not get sync state for node LTENOTAREALNODE']),
    ('network status --groups notagroup', [0], ['Invalid group arguments: notagroup']),
    ('network status --groups fm,cm.pm', [0], ['Invalid group', 'cm.pm']),
    #
    # CASE 3: network sync, sync-list
    #
    # scenario: valid arguments
    ('network sync {0}'.format(NODE_REGEX), [0, 1], []),
    ('network netsync', [0, 1], []),
    ('network netsync cm', [0, 1], []),
    ('network netsync cm,pm', [0, 1], []),
    ('network status --sl', [0], []),
    # scenario: invalid arguments
    ('network sync', [2], []),
    ('network sync NOTAREGEX', [2, 5], [ZERO_INSTANCES]),
    ('network sync-list LTENOTAREALNODE,LTENOTAREALNODE', [2, 5], []),
    #
    # CASE 3: network clear
    #
    # scenario: valid arguments
    ('network clear', [], ["NETWORK DELETION"]),
    ('cli_app "cmedit get * SubNetwork -cn"', [], [ZERO_INSTANCES.replace(' found', '')])
)
