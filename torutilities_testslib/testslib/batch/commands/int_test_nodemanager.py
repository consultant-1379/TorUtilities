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

HOSTNAME = "localhost"
PORT = 5002
API_VERSION = "/api/v1"
HEADER = "Content-Type: application/json"
VALIDATE_JSON_CMD = "python -m json.tool"

STATUS_URL = "http://{0}:{1}/status".format(HOSTNAME, PORT)
BASE_URL = "http://{0}:{1}{2}".format(HOSTNAME, PORT, API_VERSION)

LIST_NODES_URL = "{0}/nodes/list".format(BASE_URL)
CURL_POST_BASE_CMD = "curl -s -H '{0}' -X POST -d '{1}' {2} -H 'accept: application/json'"

LIST_NODES_RESP = '{"message": {"node_data": [], "node_count_from_query": 0, "total_node_count": 0}, "success": true}'
LIST_NODES_DATA_ALL = '{"profile": "None", "match_patterns": "None"}'
LIST_NODES_DATA_PROFILE = '{"profile": "TEST_00", "match_patterns": "None"}'
LIST_NODES_DATA_PATTERN = '{"profile": "None","match_patterns": "*ode2*,*ode1"}'
SLEEP_CMD = "sleep 30"
STATUS_CMD = "service nodemanager status"

commands = (
    # Command            Expected return codes       Expected strings in stdout
    # #########################################################################

    # CLEANUP
    # Clean up prior to running any tests if required
    #

    # #########################################################################
    ('/bin/echo "INTERNAL - NODEMANAGER SERVICE TESTS"', [], []),
    ('/bin/touch /home/enmutils/.install_running', [], []),

    # TESTS: nodemanager_service init.d interface
    # Tests Description:
    #       Verify that nodemanager init.d interfaces work as expected
    #
    ("service nodemanager restart", [0], ["Starting workload service nodemanager"]),
    (SLEEP_CMD, [0], []),

    (STATUS_CMD, [0], ["Service nodemanager is running"]),

    ("service nodemanager stop", [0], ["Stopping workload service nodemanager"]),

    (STATUS_CMD, [1], ["Process not running"]),

    ("service nodemanager start", [0], ["Starting workload service nodemanager"]),

    (SLEEP_CMD, [0], []),

    (STATUS_CMD, [0], ["Service nodemanager is running"]),

    ("service nodemanager restart", [0], ["Stopping workload service nodemanager",
                                          "Starting workload service nodemanager"]),

    (SLEEP_CMD, [0], []),

    (STATUS_CMD, [0], ["Service nodemanager is running"]),

    # TESTS: nodemanager_service REST interfaces
    # Tests Description:
    #       Verify that nodemanager REST interfaces work as expected
    #
    ("curl -s {0}".format(STATUS_URL), [0], ["Service nodemanager is running"]),

    (CURL_POST_BASE_CMD.format(HEADER, LIST_NODES_DATA_ALL, LIST_NODES_URL), [0], [LIST_NODES_RESP]),

    (CURL_POST_BASE_CMD.format(HEADER, LIST_NODES_DATA_PROFILE, LIST_NODES_URL), [0], [LIST_NODES_RESP]),

    (CURL_POST_BASE_CMD.format(HEADER, LIST_NODES_DATA_PATTERN, LIST_NODES_URL), [0], [LIST_NODES_RESP]),

    ('/bin/rm -f /home/enmutils/.install_running', [], [])

)
