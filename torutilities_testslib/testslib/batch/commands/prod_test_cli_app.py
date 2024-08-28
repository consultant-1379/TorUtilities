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

CONCURRENT_RUN = False

# ADD expected strings to the stdout list

commands = (
    # Command            Expected return codes       Expected strings in stdout
    # #########################################################################

    # CLEANUP
    # Clean up prior to running any tests if required
    #
    ('/bin/echo "PROD - CLI APP TOOL TEST"', [], []),
    ('/bin/rm -rf /tmp/torutilities/*', [], []),
    # #########################################################################

    # TESTS 4
    # Tests Description:
    #       Verify that all cli_app commands work as expected
    #
    # CASE 1: cli_app
    #
    # scenario: cli_app get operations
    ('cli_app "no command" extra_argument', [2], []),
    ('cli_app --list', [0], []),
    ('cli_app "cmedit get * MeContext"', [0], []),
    ('cli_app "cmedit get * NetworkElement"', [0], []),
    ('cli_app "cmedit get * FmAlarmSupervision.*"', [0], []),
    #
    ('cli_app --list', [0], []),
    #
    ('cli_app "cmedit describe FmAlarmSupervision.*"', [0], []),
    ('cli_app "cmedit describe NetworkElement.*"', [0], []),
    ('cli_app "cmedit describe MeContext.*"', [0], []),
    #
    ('cli_app "cmedit get * MeContext.*" --save cmedit_get', [0], []),
    ('cli_app "cmedit get * MeContext.*" --save cmedit_get extra junk', [2], []),
    ('cli_app "cmedit get * MeContext.*" --save', [2], []),
    ('cli_app -s cmedit_get', [0], []),
    ('cli_app -s cmedit_get extra junk', [2], []),
    #
    ('persistence remove cli_saved_searches', [0], []),
    ('cli_app -s', [2], []),
    ('cli_app -s cmedit_get', [2], []),
    ('cli_app "cmedit describe MeContext.*"', [0], []),
    ('cli_app --list', [0], []),
)
