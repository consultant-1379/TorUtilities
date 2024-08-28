"""
This file can be used to run all batch_runner tests for all the internal tools
to run: batch_runner <path-to>/internal.py

Tests for internal tools starts with 'int_test_<tool_name>.py' and can be found in:
TorUtilities/ERICtorutilitiesinternal_CXP9030579/enmutils_int/tests/batch/commands/ dir

"""
from enmutils_int.bin.batch_runner import get_commands_tuples_for_tools


# this will be returned to batch_runner
commands = get_commands_tuples_for_tools(tools='int')
