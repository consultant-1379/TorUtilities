"""
This file can be used to run all batch_runner tests for the production tool
to run: batch_runner <path-to>/production.py

Tests for production tools starts with 'prod_test_<tool_name>.py' and can be found in:
TorUtilities/ERICtorutilitiesinternal_CXP9030579/enmutils_int/tests/batch/commands/ dir

"""
from enmutils_int.bin.batch_runner import get_commands_tuples_for_tools


# this will be returned to batch_runner
commands = get_commands_tuples_for_tools(tools='prod')
