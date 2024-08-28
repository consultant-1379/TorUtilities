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
PORT = 5004
API_VERSION = "/api/v1"
HEADER = "Content-Type: application/json"

STATUS_URL = "http://{0}:{1}/status".format(HOSTNAME, PORT)
BASE_URL = "http://{0}:{1}{2}/deployment".format(HOSTNAME, PORT, API_VERSION)

APACHE_URL = "{0}/apache".format(BASE_URL)
SERVICE_INFO_URL = "{0}/info".format(BASE_URL)
READ_PIB_URL = "{0}/pib/read".format(BASE_URL)
UPDATE_PIB_URL = "{0}/pib/update".format(BASE_URL)
POID_REFRESH_URL = "{0}/poid_refresh".format(BASE_URL)
COPY_EMP_URL = "{0}/copy_emp".format(BASE_URL)
ENM_ACCESS_URL = "{0}/enm/access".format(BASE_URL)
PASS_AGEING_URL = "{0}/password/ageing".format(BASE_URL)
DEPLOYMENT_CONFIG = "{0}/config".format(BASE_URL)

SERVICE_NAME = "deploymentinfomanager"
SERVICE_CMD_BASE = "service {0}".format(SERVICE_NAME)
SERVICE_CMD_START = "{0} start".format(SERVICE_CMD_BASE)
SERVICE_CMD_STOP = "{0} stop".format(SERVICE_CMD_BASE)
SERVICE_CMD_RESTART = "{0} restart".format(SERVICE_CMD_BASE)
SERVICE_CMD_STATUS = "{0} status".format(SERVICE_CMD_BASE)

SVC_STARTING_STRING = "Starting workload service {0}".format(SERVICE_NAME)
SVC_RUNNING_STRING = "Service {0} is running".format(SERVICE_NAME)


SERVICE_INFO_DATA = '{"enm_value": "dps_persistence_provider"}'
SERVICE_PIB_READ_DATA = ('{"enm_service_name": "cmserv", "pib_parameter_name": "maxAmosSessions", '
                         '"service_identifier": "terminal-websocket"}')
SERVICE_PIB_UPDATE_DATA = ('{"enm_service_name": "cmserv", "pib_parameter_name": "maxAmosSessions", '
                           '"pib_parameter_value":150, "service_identifier": "terminal-websocket", '
                           '"scope": "GLOBAL"}')
SERVICE_LMS_PASS_DATA = '{"username": "user", "password": "pass", "ms_host": "host"}'
CURL_POST_BASE_CMD = "curl -s -H '{0}' -X POST -d '{1}' {2} -H 'accept: application/json'"
CURL_GET_BASE_CMD = "curl -s -X GET {0} -H 'accept: application/json'"
MSG_SUCCESS = '{"message": "", "success": true}'
POID_MSG = '{"message": "120", "success": true}'

WORKLOAD_TOOL = "/opt/ericsson/enmutils/bin/workload"
commands = (
    # Command            Expected return codes       Expected strings in stdout
    # #########################################################################

    # CLEANUP
    # Clean up prior to running any tests if required
    #
    ("{0} reset".format(WORKLOAD_TOOL), [], []),
    ("{0} remove all".format(WORKLOAD_TOOL), [], []),
    # #########################################################################
    ('/bin/echo "INTERNAL - DEPLOYMENTINFOMANAGER SERVICE TESTS"', [], []),

    # TESTS: nodemanager_service init.d interface
    # Tests Description:
    #       Verify that nodemanager init.d interfaces work as expected
    #
    (SERVICE_CMD_RESTART, [0], [SVC_STARTING_STRING]),

    (SERVICE_CMD_STATUS, [0], [SVC_RUNNING_STRING]),

    (SERVICE_CMD_STOP, [0], ["Stopping workload service {0}".format(SERVICE_NAME)]),

    (SERVICE_CMD_STATUS, [1], ["Process not running"]),

    (SERVICE_CMD_START, [0], [SVC_STARTING_STRING]),

    (SERVICE_CMD_STATUS, [0], ["Service {0} is running".format(SERVICE_NAME)]),

    (SERVICE_CMD_RESTART, [0], ["Stopping workload service {0}".format(SERVICE_NAME), SVC_STARTING_STRING]),

    (SERVICE_CMD_STATUS, [0], [SVC_RUNNING_STRING]),

    # TESTS: deploymentinfomanager REST interfaces
    # Tests Description:
    #       Verify that deploymentinfomanager REST interfaces work as expected
    #
    ("curl -s {0}".format(STATUS_URL), [0], [SVC_RUNNING_STRING]),
    (CURL_GET_BASE_CMD.format(APACHE_URL), [0], ["apache_url"]),
    (CURL_POST_BASE_CMD.format(HEADER, SERVICE_INFO_DATA, SERVICE_INFO_URL), [0],
     ['{"message": {"service_info": ["neo4j"]}, "success": true}']),
    (CURL_POST_BASE_CMD.format(HEADER, SERVICE_PIB_READ_DATA, READ_PIB_URL), [0], [POID_MSG]),
    (CURL_POST_BASE_CMD.format(HEADER, SERVICE_PIB_UPDATE_DATA, UPDATE_PIB_URL), [0], [MSG_SUCCESS]),
    (CURL_POST_BASE_CMD.format(HEADER, SERVICE_PIB_READ_DATA, READ_PIB_URL), [0],
     ['{"message": "150", "success": true}']),
    (CURL_POST_BASE_CMD.format(HEADER, SERVICE_PIB_UPDATE_DATA.replace('150', '120'), UPDATE_PIB_URL), [0],
     [MSG_SUCCESS]),
    (CURL_POST_BASE_CMD.format(HEADER, SERVICE_PIB_READ_DATA, READ_PIB_URL), [0],
     [POID_MSG]),
    (CURL_GET_BASE_CMD.format(POID_REFRESH_URL), [0], ['"success": true']),
    (CURL_GET_BASE_CMD.format(COPY_EMP_URL), [0], ["Successfully copied ENM key pair to EMP."]),
    (CURL_GET_BASE_CMD.format(ENM_ACCESS_URL), [0], ['{"message": {"log_info": "Workload VM has access to vENM", '
                                                     '"enm_access": true}, "success": true}']),
    (CURL_GET_BASE_CMD.format(PASS_AGEING_URL), [0], []),
    (CURL_GET_BASE_CMD.format(DEPLOYMENT_CONFIG), [0], [])
)
