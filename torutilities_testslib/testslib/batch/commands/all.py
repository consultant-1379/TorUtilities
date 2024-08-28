"""
This file can be used to run all batch_runner tests
to run: batch_runner <path-to>/all.py

Tests for all tools can be found in:
TorUtilities/ERICtorutilitiesinternal_CXP9030579/enmutils_int/tests/batch/commands/

"""
from enmutils_int.bin.batch_runner import get_commands_tuples_for_tools


# this will be returned to batch_runner
commands = get_commands_tuples_for_tools(tools='prod')
commands.extend(get_commands_tuples_for_tools(tools='int'))
