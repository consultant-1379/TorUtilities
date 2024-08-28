#!/usr/bin/env python
from __future__ import print_function

import os
import types
import sys
import shutil
from datetime import datetime, timedelta


def main(config_path, high_priority_file=None, low_priority_file=None):
    """
    Prepend timestamps every rop time to the dummy files and copy those to the simulation
    db dirs
    """
    celltrace_config = _get_module_from_file(config_path)

    if not low_priority_file:
        low_priority_file = getattr(celltrace_config, 'LOW_PRIORITY_FILE', None)
    if not high_priority_file:
        high_priority_file = getattr(celltrace_config, 'HIGH_PRIORITY_FILE', None)
    rop_info = int(getattr(celltrace_config, 'ROP_INFO', '15'))
    simulations = getattr(celltrace_config, 'SIMULATIONS')
    db_dir = getattr(celltrace_config, 'DB_DIR')

    now = datetime.now()
    start = now - timedelta(minutes=rop_info)
    end = now

    prepend_time_stamp = "A{0}-{1}".format(start.strftime("%Y%m%d.%H%M"), end.strftime("%H%M"))

    low_priority_filename = prepend_time_stamp + '_CellTrace_DUL1_1.bin.gz'
    high_priority_filename = prepend_time_stamp + '_CellTrace_DUL1_3.bin.gz'

    for simulation, nodes in simulations.items():
        for node in nodes:
            destination = os.path.join(db_dir, simulation, node.split('_')[1], 'fs', 'c', 'pm_data')
            if low_priority_file:
                shutil.copyfile(low_priority_file, os.path.join(destination, low_priority_filename))
            if high_priority_file:
                shutil.copyfile(high_priority_file, os.path.join(destination, high_priority_filename))


def _get_module_from_file(python_file_path):
    """
    Open python file and read all the attributes in a new module and return the module
    """
    d = types.ModuleType('config')
    d.__file__ = python_file_path
    with open(python_file_path) as config_file:
        exec(compile(config_file.read(), python_file_path, 'exec'), d.__dict__)
    return d


def _print_help():
    print(
        "  USAGE: ./cell_trace_update.py <config_file> <high_priority_file> <low_priority_file>\n\n"
        "     Tool takes three optional parameter <config_file> which will be a path to\n"
        "     the config file for this tool. The configuration file should be a python file\n"
        "     with valid parameters DB_DIR, ROP_INFO, CELLTRACE_PATH, SUMULATIONS,\n"
        "     LOW_PRIORITY_FILE, HIGH_PRIORITY_FILE. Example of such file is:\n"
        "     <!----\n"
        "       DB_DIR = '/netsim/db_dir/'  # Path to db folder on netsim\n"
        "       ROP_INFO = '15'  # Rop timings in minutes\n"
        "       CELLTRACE_PATH = '/netsim/netsim_users/' # Path to the celltrace files\n"
        "       SIMULATIONS = {'netsimlin704': {'LTEE01': ['node1', 'node2', 'node3']}}  # Simulations\n"
        "       LOW_PRIORITY_FILE='/netsim/netsim_users/celltrace_256k.bin.gz'\n"
        "       HIGH_PRIORITY_FILE='/netsim/netsim_users/celltrace_4.7M.bin.gz'\n"
        "     -->\n"
        "     Examples:\n"
        "         ./cell_trace_update.py /tmp/test_config.py\n"
        "         ./cell_trace_update.py /tmp/test_config.py /netsim/netsim_users/celltrace_4.7M.bin.gz\n"
        "         ./cell_trace_update.py /tmp/test_config.py /netsim/netsim_users/celltrace_4.7M.bin.gz /netsim/netsim_users/celltrace_256k.bin.gz\n"
        "         ./cell_trace_update.py\n"
    )


if __name__ == '__main__':
    config_file = None
    low_priority_file = high_priority_file = None

    if len(sys.argv) > 4 or len(sys.argv) < 2:
        _print_help()
        sys.exit(1)

    if sys.argv[1] in ['-h', '--help']:
        _print_help()
        sys.exit(0)

    config_file = sys.argv[1]

    if len(sys.argv) == 4:
        high_priority_file = sys.argv[2]
        low_priority_file = sys.argv[3]
    elif len(sys.argv) == 3:
        high_priority_file = sys.argv[2]

    main(config_file, high_priority_file, low_priority_file)
