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
# select small simulation when possible with ERBS nodes
simulations = [sim for sim in list_netsim_simulations() if 'LTE' in sim and 'limx40' in sim]
simulation = simulations[0] if simulations else 'ERROR: COULD NOT MATCH ANY SIMULATION'
node_dir = 'workload_nodes'
num_nodes = 3
NSSUTILS_TOOL_LOCATION = "/opt/ericsson/nssutils/bin/"

commands = (
    # Command            Expected return codes       Expected strings in stdout
    # #########################################################################

    # CLEANUP
    # Clean up prior to running any tests if required
    ('/bin/echo "INTERNAL - CONSISTENCY TOOL TEST"', [], []),
    # setup simulations and prepare node pool
    ('{2}node_populator unmanage {0} 1-{1}'.format(node_dir, num_nodes, NSSUTILS_TOOL_LOCATION), [], []),
    ('{2}node_populator delete {0} 1-{1}'.format(node_dir, num_nodes, NSSUTILS_TOOL_LOCATION), [], []),
    # remove enmutils directories
    ('/bin/rm -rf /tmp/torutilities /tmp/enmutils {0}'.format(node_dir), [0], []),
    # start simulation & setup network
    ('{1}netsim start netsim {0}'.format(simulation, NSSUTILS_TOOL_LOCATION), [0], []),
    ('{2}netsim fetch netsim {0} {1}'.format(simulation, node_dir, NSSUTILS_TOOL_LOCATION), [0], []),
    ('{1}node_populator parse {0} {0}'.format(node_dir, NSSUTILS_TOOL_LOCATION), [0], []),
    ('{2}node_populator create {0} 1-{1}'.format(node_dir, num_nodes, NSSUTILS_TOOL_LOCATION), [], []),
    ('workload add /opt/ericsson/nssutils/etc/nodes/{0}'.format(node_dir), [], []),

    # #########################################################################

    # TESTS 4 consistency
    # Tests Description:
    #       Verify that workload pool versus ENM is consistent
    #
    # CASE 1: consistency check
    #
    # scenario: valid arguments
    ('consistency -h', [0], []),
    ('consistency check', [0], []),
    ('consistency check --enm', [0], []),
    ('consistency check --show-nodes', [0], []),

    # scenario: invalid arguments
    ('consistency --enm', [2], ['Invalid command line arguments']),
    #
    # CASE 2: consistency resolve
    #
    ('consistency resolve', [0], []),
    ('consistency resolve --delete-from-enm', [0], []),

    # scenario: invalid arguments
    ('consistency resolve all', [2], ['Invalid command line arguments']),
    #
    #
    # CASE 3: consistency display
    #
    ('consistency display', [0], ['Total available']),
    ('consistency display ERBS,MGW', [0, 1], ['Total available']),

    # scenario: invalid arguments
    ('consistency ERBS,MGW', [2], ['Invalid command line arguments']),
    #

)
