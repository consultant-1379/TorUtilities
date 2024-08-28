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

commands = (
    # Command            Expected return codes       Expected strings in stdout
    # #########################################################################

    # CLEANUP
    # Clean up prior to running any tests if required
    #
    ('/bin/echo "PROD - PERSISTENCE TOOL TEST"', [], []),
    ('/bin/rm -rf /tmp/torutilities/*', [], []),
    # Clear persistence
    ('persistence clear', [0], []),
    ('persistence clear force --auto-confirm', [0], []),
    ('persistence clear force --index=99', [0], []),
    # #########################################################################

    # TESTS 4 persistence
    # Tests Description:
    #       Verify that all persistence commands work as expected
    #
    # CASE 1: persistence set, get, remove
    #
    # scenario: valid arguments
    ('persistence get batch_run_commands_key_2', [1], ['was not found']),
    ('persistence set batch_run_commands_key_1 batch_run_commands_value_1 50', [0], ['result was successful', 'persisting']),
    ('persistence get batch_run_commands_key_1', [0], ['batch_run_commands_key_1 = batch_run_commands_value_1']),
    ('persistence get batch_run_commands_key_1 --json', [0], ['batch_run_commands_value_1']),
    ('persistence remove batch_run_commands_key_1', [0], ['operation REMOVE', 'result was successful']),
    ('persistence set batch_run_commands_key_2 batch_run_commands_value_2 indefinite', [0], ['operation SET', 'result was successful']),
    ('persistence get batch_run_commands_key_2', [0], ['batch_run_commands_key_2 = batch_run_commands_value_2']),
    (""" python -c "from datetime import datetime;from enmutils.lib import log,persistence;log.log_init();persistence.set('test_batch_runner', [{'test_set'}, datetime(2020, 12, 12)], 100)" """, [0], []),
    ('persistence get test_batch_runner --json', [0], ['["test_set"]', '2020-12-12 00:00:00']),
    ('persistence get test_batch_runner --detailed', [0], ["set(['test_set'])", 'datetime.datetime(2020, 12, 12, 0, 0)']),
    ('persistence get test_batch_runner --json --detailed', [0], ['["test_set"]', '2020-12-12 00:00:00']),
    ('persistence remove test_batch_runner', [0], ['operation REMOVE', 'result was successful']),
    #
    # scenario: invalid arguments
    ('persistence set batch_run_commands_key_3 batch_run_commands_value_3 10 extra_argument', [2], ['ERROR', 'validation has failed']),
    ('persistence set batch_run_commands_key_4', [2], ['ERROR', 'validation has failed']),
    ('persistence set batch_run_commands_key_5 some_value bad_expiry_value', [2], ['ERROR', 'validation has failed']),
    ('persistence set batch_run_commands_key_5 batch_run_commands_value_5 --index=blah', [2], ['ERROR', 'validation has failed']),
    #
    # CASE 3: persistence set, list
    #
    # scenario: list all keys with TOKEN: test
    ('persistence set batch_run_commands_test_1 some_value indefinite', [0], ['result was successful']),
    ('persistence set batch_run_commands_test_2 some_value indefinite', [0], ['result was successful']),
    ('persistence set batch_run_commands_test_3 some_value indefinite', [0], ['result was successful']),
    ('persistence set batch_run_commands_test_4 some_value indefinite', [0], ['result was successful']),
    ('persistence list test', [0], ['batch_run_commands_test_1', 'batch_run_commands_test_2', 'batch_run_commands_test_3', 'batch_run_commands_test_4']),
    #
    # CASE 4: persistence remove, clear
    #
    # scenario: valid arguments
    ('persistence clear', [0], []),
    ('persistence list test', [0], ['batch_run_commands_test_1', 'batch_run_commands_test_2', 'batch_run_commands_test_3', 'batch_run_commands_test_4']),
    ('persistence clear force --auto-confirm', [0], []),
    # scenario: invalid arguments
    ('persistence set batch_run_commands_key_3 batch_run_commands_value_3 10 extra_argument', [2], ['ERROR', 'validation has failed']),
    ('persistence set batch_run_commands_key_4', [2], ['ERROR', 'validation has failed']),
    ('persistence set batch_run_commands_key_5 some_value bad_expiry_value', [2], ['ERROR', 'validation has failed']),
    ('persistence set batch_run_commands_key_5 batch_run_commands_value_5 --index=blah', [2], ['ERROR', 'validation has failed']),
    #
    # CASE 5: persistence set, get, clear, remove by index
    #
    # scenario: valid arguments
    ('persistence get batch_run_commands_key_2 --index=99', [1], ['was not found']),
    ('persistence set batch_run_commands_key_1 batch_run_commands_value_1 50 --index=99', [0], ['result was successful']),
    ('persistence set batch_run_commands_test_1 some_value indefinite --index=99', [0], ['result was successful']),
    ('persistence get batch_run_commands_key_1 --index=99', [0], ['batch_run_commands_key_1 = batch_run_commands_value_1']),
    ('persistence get batch_run_commands_key_1 --json --index=99', [0], ['batch_run_commands_value_1']),
    ('persistence list --index=99', [0], ['batch_run_commands_key_1', 'batch_run_commands_test_1']),
    ('persistence clear --index=99', [0], []),
    ('persistence get batch_run_commands_key_1 --index=99', [1], ['was not found']),
    ('persistence get batch_run_commands_test_1 --index=99', [0], ['batch_run_commands_test_1 = some_value']),
    ('persistence get batch_run_commands_test_1 --json --index=99', [0], ['some_value']),
    ('persistence clear force --index=99', [0], []),
    ('persistence get batch_run_commands_test_1 --index=99', [1], ['was not found']),
    # scenario: invalid arguments
    ('persistence set batch_run_commands_key_1 batch_run_commands_value_1 50 --index=-1', [2], ['The index you specified is not valid']),
    ('persistence get batch_run_commands_key_1 --index=-1', [2], ['The index you specified is not valid']),
    ('persistence list --index=-1', [2], ['The index you specified is not valid']),
    ('persistence remove batch_run_commands_key_1 --index=-1', [2], ['The index you specified is not valid']),
    ('persistence clear force --index=-1', [2], ['The index you specified is not valid'])

)
