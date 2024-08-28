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

commands = (
    # Command            Expected return codes       Expected strings in stdout
    # #########################################################################

    # CLEANUP
    # Clean up prior to running any tests if required
    #

    ('/bin/echo "INTERNAL - USER MANAGER TOOL TEST"', [], []),
    ('/bin/rm -rf /tmp/torutilities/*', [], []),
    ('user_mgr list', [0], []),
    ('user_mgr delete nightrider_user', [], []),
    ('user_mgr delete single_nightrider_user', [], []),

    # #########################################################################

    # TESTS 4 user_mgr
    # Tests Description:
    #       Verify that all user_mgr commands work as expected
    #
    # CASE 1: user_mgr create
    #
    # scenario: invalid arguments
    ('user_mgr create', [2], ['ERROR', 'validation has failed']),
    ('user_mgr create nightrider_user', [2], ['ERROR', 'validation has failed']),
    ('user_mgr create nightrider_user Enmuser42', [2], ['ERROR', 'validation has failed']),
    ('user_mgr create nightrider_user Enmuser42 Enm User', [2], ['ERROR', 'validation has failed']),
    ('user_mgr create nightrider_user Enmuser42 OPERATOR Enm', [2], ['ERROR', 'validation has failed']),
    ('user_mgr create nightrider_user Enmuser42 OPERATOR --verbose invalid', [2], ['ERROR', 'validation has failed']),
    ('user_mgr create nightrider_user Enmuser42 OPERATOR, ADMINISTRATOR', [2], ['ERROR', 'validation has failed']),
    ('user_mgr create nightrider_user Enmuser42 OPERATOR, ADMINISTRATOR 1-2', [2], ['ERROR', 'validation has failed']),
    ('user_mgr create nightrider_user Enmuser42 OPERATOR, ADMINISTRATOR 1-2 --verbose', [2], ['ERROR', 'validation has failed']),
    #
    # CASE 2: user_mgr delete
    #
    # scenario: invalid arguments
    ('user_mgr delete nightrider_user Enmuser42', [2], ['ERROR', 'validation has failed']),
    ('user_mgr delete nightrider_user unknown 1', [2], ['ERROR', 'validation has failed']),
    ('user_mgr delete nightrider_user 2 unknown invalid', [2], ['ERROR', 'validation has failed']),
    #
    # CASE 3: user_mgr create & delete
    #
    # scenario: valid arguments
    ('user_mgr create single_nightrider_user Enmuser42 ADMINISTRATOR', [0], ['Attempting to create', 'Successfully completed', 'USERS CREATED: 1/1']),
    ('user_mgr delete single_nightrider_user', [0], ['Attempting to delete', 'Successfully', 'USERS DELETED: 1/1']),
    ('user_mgr create nightrider_user Enmuser42 OPERATOR Enm User EnmUser@ericsson.com', [0], ['Attempting to create',
                                                                                               'Successfully completed', 'USERS CREATED: 1/1']),
    ('user_mgr delete nightrider_user', [0], ['Attempting to delete', 'Successfully', 'USERS DELETED: 1/1']),
    ('user_mgr create nightrider_user Enmuser42 SECURITY_ADMIN,OPERATOR,ADMINISTRATOR,Cmedit_Administrator,Cmedit_Operator,Shm_Administrator,Shm_Operator',
     [0], ['Successfully completed', 'USERS CREATED: 1/1']),
    ('user_mgr delete nightrider_user', [0], ['Attempting to delete', 'Successfully', 'USERS DELETED: 1/1']),
    ('user_mgr delete nightrider_user', [1], ['not on the system']),
    #
    # CASE 4: user_mgr create & delete using --file
    #
    # scenario: valid arguments
    ('/usr/bin/printf "USERNAME,FIRSTNAME,LASTNAME,EMAIL,ROLES\nenm_user1,joe,bloggs,joe.bloggs@ericsson.com,ADMINISTRATOR,OPERATOR\nenm_user2,jane,doe,jane.doe@ericsson.com,ADMINISTRATOR" > /tmp/torutilities_users_list', [0], []),
    ('user_mgr create --file /tmp/torutilities_users_list TestPassw0rd', [0], ['Successfully', 'USERS CREATED: 2/2']),
    ('user_mgr delete --file /tmp/torutilities_users_list', [0], ['Attempting to delete', 'Successfully', 'USERS DELETED: 2/2']),
    ('/bin/rm -f /tmp/torutilities_users_list', [0], []),
    ('user_mgr list', [0], ['USERS']),
    #
    # CASE 5: user_mgr list
    #
    # scenario: valid arguments
    ('user_mgr list', [0], ['USERS']),
    # no user exists but next cmd returns 0 anyway
    ('user_mgr list nightrider_user', [0], ['NUMBER OF USERS LISTED: 0/']),
)
