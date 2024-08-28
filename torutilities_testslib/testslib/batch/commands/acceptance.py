"""
This file is designed be run by batch_runner tool
to run: batch_runner <path-to>/acceptance.py

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

Example:
commands = (
    ('/home/me/workspace/TorUtilities/ERICtorutilitiesinternal_CXP9030579/enmutils_int/tests/acceptance/a_tests_http.py', [0]),
    ('/home/me/workspace/TorUtilities/ERICtorutilitiesinternal_CXP9030579/enmutils_int/tests/acceptance/a_tests_remote_shell.py', [0]),
    ('/home/me/workspace/TorUtilities/ERICtorutilitiesinternal_CXP9030579/enmutils_int/tests/acceptance/a_tests_ui_fm_alarm_route_policy.py', [0])
    )
"""
import pkgutil
from os import walk

import unipath


def get_acceptance_tests_with_return_code_tuple():
    """
    Build a tuple with all acceptance tests and corresponding return code.
    Tuple is formatted in the way that can be used by batch_runner tool.
    Return code is assumed to be 0
    :rtype: tuple
    :returns: Tuple containing list of acceptance modules
    """
    ENMUTILS_INT_PATH = unipath.Path(pkgutil.get_loader('enmutils_int').filename)
    TESTS_PATH = ENMUTILS_INT_PATH.child('tests')
    TESTS_ACCEPTANCE_PATH = TESTS_PATH.child('acceptance')

    ac_tests_formatted = []

    # query for all AC tests and prepare data structure for batch_runner
    for (_, _, filenames) in walk(TESTS_ACCEPTANCE_PATH):
        for test in filenames:
            ac_tests_formatted.append(tuple(
                ['{0}/{1}'.format(TESTS_ACCEPTANCE_PATH, test), [0], []]))
    return tuple(ac_tests_formatted)


# this will be returned to batch_runner
commands = get_acceptance_tests_with_return_code_tuple()

if __name__ == '__main__':
    print get_acceptance_tests_with_return_code_tuple()
