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
PORT = 5001
API_VERSION = "/api/v1"
HEADER = "Content-Type: application/json"

STATUS_URL = "http://{0}:{1}/status".format(HOSTNAME, PORT)
BASE_URL = "http://{0}:{1}{2}".format(HOSTNAME, PORT, API_VERSION)
SWAGGER_URL = "{0}/docs/".format(BASE_URL)
LIST_USERS_URL = "{0}/users".format(BASE_URL)
LIST_USERS_ON_ENM_URL = "{0}/enm/users".format(BASE_URL)
GET_USERNAME = "USERNAME=$(curl -s {0}?profile=TEST_USER | python -m json.tool | egrep username | awk -F '\"' '{{print $(NF-1)}}')".format(LIST_USERS_URL)
GET_USER_BY_USERNAME = " {0}; curl -s {1}?username=$USERNAME".format(GET_USERNAME, LIST_USERS_URL)

CREATE_USERS_URL = "{0}/users/create".format(BASE_URL)
CREATE_USERS_DATA = '{"username_prefix": "TEST_USER", "number_of_users": 1, "user_roles": ["PM_Operator"]}'

DELETE_USERS_URL = "{0}/users/delete".format(BASE_URL)
DELETE_USERS_DATA = '{"username_prefix": "TEST_USER"}'
DELETE_USERS_DATA_ALL = '{"username_prefix": ""}'

commands = (
    # Command            Expected return codes       Expected strings in stdout
    # #########################################################################

    # CLEANUP
    # Clean up prior to running any tests if required
    #

    # #########################################################################
    ('/bin/echo "INTERNAL - USERMANAGER SERVICE TESTS"', [], []),
    ('/bin/touch /home/enmutils/.install_running', [], []),

    # TESTS: usermanager_service init.d interface
    # Tests Description:
    #       Verify that usermanager init.d interfaces work as expected
    #
    ("service usermanager restart", [0], ["Starting workload service usermanager"]),

    ("service usermanager status", [0], ["Service usermanager is running"]),

    ("service usermanager stop", [0], ["Stopping workload service usermanager"]),

    ("service usermanager status", [1], ["Process not running"]),

    ("service usermanager start", [0], ["Starting workload service usermanager"]),

    ("service usermanager status", [0], ["Service usermanager is running"]),

    ("service usermanager restart", [0], ["Stopping workload service usermanager",
                                          "Starting workload service usermanager"]),

    ("service usermanager status", [0], ["Service usermanager is running"]),

    # TESTS: usermanager_service REST interfaces
    # Tests Description:
    #       Verify that usermanager REST interfaces work as expected
    #
    ("curl -s {0}".format(STATUS_URL), [0], ["Service usermanager is running"]),
    ("curl -sI {0}".format(SWAGGER_URL), [0], ["200 OK"]),
    ("curl -sI {0}{1}.json".format(SWAGGER_URL, 'usermanager'), [0], ["200 OK"]),
    ("curl -s -H '{0}' -X DELETE -d '{1}' {2}".format(HEADER, DELETE_USERS_DATA_ALL,
                                                      DELETE_USERS_URL), [0], ['{"message": "", "success": true}']),

    ("curl -s {0}".format(LIST_USERS_URL), [0], []),

    # APT team uses below endpoint to create a user. If there are any changes made to this endpoint API, please inform them before merging
    ("curl -s -H '{0}' -X POST -d '{1}' {2}".format(HEADER, CREATE_USERS_DATA, CREATE_USERS_URL), [0], []),

    ("curl -s {0}".format(LIST_USERS_URL), [0], ["TEST_USER", "TestPassw0rd"]),
    ("curl -s {0}?profile=TEST_USER".format(LIST_USERS_URL), [0], ["TEST_USER", "TestPassw0rd"]),
    (GET_USER_BY_USERNAME, [], ["TEST_USER", "TestPassw0rd"]),
    # APT team uses below endpoint to get enm users. If there are any changes made to endpoint this API, please inform them before merging
    ("curl -s {0}".format(LIST_USERS_ON_ENM_URL), [0], ["TEST_USER", "administrator"]),

    ("curl -s -H '{0}' -X DELETE -d '{1}' {2}".format(HEADER, DELETE_USERS_DATA,
                                                      DELETE_USERS_URL), [0], ['{"message": "", "success": true}']),

    ("curl -s {0}".format(LIST_USERS_URL), [0], []),
    ('/bin/rm -f /home/enmutils/.install_running', [], [])
)
