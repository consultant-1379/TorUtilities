#!/usr/bin/env python
# ********************************************************************
# Ericsson LMI                 Utility Script
# ********************************************************************
#
# (c) Ericsson LMI 2014 - All rights reserved.
#
# The copyright to the computer program(s) herein is the property of Ericsson
# LMI. The programs may be used and/or copied only with the written permission
# from Ericsson LMI or in accordance with the terms and conditions stipulated
# in the agreement/contract under which the program(s) have been supplied.
#
# ********************************************************************
# Name    : basic_net_update
# Purpose : Tool to increment the update version value for profile restart
# Team    : Blade Runners
# ********************************************************************

"""
basic_net_update - Tool to increment the update version value, on basic_network.py, for profile restart

Usage:
    basic_net_update update [PROFILES] [-a | --inc-all]

Arguments:
    PROFILES        Categories or profiles to increment

Options:
    -a, --inc-all       Includes both supported and unsupported profiles

Examples:
    ./basic_net_update update
        Increments the update version value of all supported profiles

    ./basic_net_update update amos,cmimport
        Increments the update version value of all supported amos and cmimport profiles

    ./basic_net_update update amos_01,amos_02
        Increments the update version value of amos_01 and amos_02, if supported.

    ./basic_net_update update amos,cmimport_01 --inc_all
        Increments the update version value of all amos and cmimport_01,disregarding the supported status.

"""
import os
import re
import sys
import signal
import shutil

from docopt import docopt

from enmutils.lib import log, init, exception
from enmutils.lib.filesystem import read_lines_from_file
from enmutils_int.lib.common_utils import get_internal_file_path_for_import
from enmutils_int.lib.services.profilemanager_helper_methods import get_categories, get_all_profile_names


def validate_line(line, inc_unsupported=False):
    """
    Checks if line should be incremented

    :param inc_unsupported: Include unsupported profiles
    :type inc_unsupported: bool
    :param line: The line to check for condition
    :type line: str

    :return: Returns true when any conditions are met
    :rtype: bool
    """
    # Excludes the unsupported profiles
    cond1 = ((not inc_unsupported) and "NOTE: MANUAL" not in line and all(
        c in line for c in ("SUPPORTED: True", "UPDATE:")))
    # Includes the unsupported profiles
    cond2 = (inc_unsupported and "UPDATE:" in line and all(
        c not in line for c in ("SUPPORTED: INTRUSIVE", "NOTE: MANUAL", "SUPPORTED: STKPI")))
    return cond1 or cond2


def increment_category(app, path, inc_unsupported=False):
    """
    Flow for the category command

    :param path: The path to the file to edit
    :type path: str
    :param inc_unsupported: Boolean to decide whether to include unsupported profiles or not
    :type inc_unsupported: bool
    :param app: The profiles to increment
    :type app: str
    """
    lines = read_lines_from_file(path)
    if app.find("_") == -1:
        app = "'" + app + "_"  # This is added to filter out partial matches, e.g. ap in apt
    with open(path, "w") as f:
        for line in lines:
            # If validate line is True and the app is found in the first 40 characters of the line, then increment
            if validate_line(line, inc_unsupported=inc_unsupported) and line.find(app, 0, 40) != -1:
                increment_update(f, line)
            # Covers lines not of interest
            else:
                f.write(line)


def increment_all(path, inc_unsupported=False):
    """
    Flow for the all command

    :param path: The path to the file to edit
    :type path: str
    :param inc_unsupported: Boolean to decide whether to include unsupported profiles or not
    :type inc_unsupported: bool
    """
    lines = read_lines_from_file(path)
    with open(path, "w") as f:
        for line in lines:
            if validate_line(line, inc_unsupported=inc_unsupported):
                increment_update(f, line)
            # Covers lines not of interest
            else:
                f.write(line)


def increment_update(basic_file, line):
    """
    Increments the update value in the line

    :param basic_file: The basic_network file
    :type basic_file: File
    :param line: The line to search
    :type line: str
    """
    old = re.search(r' \d{1,3}', line)  # searches for the first occurrence of 1/2/3 digits
    # Finds old value and increments it
    new_line = re.sub(old.group(0), " {0}".format(int(old.group(0)) + 1), line, count=1)
    basic_file.write(new_line)  # Writes the new result


def validate_arguments(categories):
    """
    Checks if the arguments(category names) are valid, and removes any duplicated names

    :param categories: A list of category or profile names
    :type categories: list

    :return: A list of valid profile names
    :rtype: list

    :raises Exception: If the profile names are invalid
    """
    # Initialising lists
    valid_cat = []
    valid_profile = []
    invalid = []

    categories = list(set(categories))  # Removing duplicates

    for category in categories:
        if category.lower() in get_categories():
            valid_cat.append(category)  # Checks against valid categories
        elif category.lower() in get_all_profile_names():
            valid_profile.append(category)  # Checks against valid profiles
        else:
            invalid.append(category)

    # Checks if any conflicts between category and profile, e.g. cmsync,cmsync_01
    conflicting_profiles = []
    for profile in valid_profile:
        for cat in valid_cat:
            if profile.find(cat) != -1:
                conflicting_profiles.append(profile)  # If a conflicting name is found, then it is added to a list

    # Deletes the conflicting profile names from valid_profile, if exist
    if conflicting_profiles:
        for profile in conflicting_profiles:
            valid_profile.remove(profile)

    # Throws an exception with the invalid profile names
    if invalid:
        raise Exception("The following names are invalid:{}".format(invalid))

    return valid_cat + valid_profile


def cli():
    # Register signal handler
    signal.signal(signal.SIGINT, init.signal_handler)
    # Initialize logging and load our configuration properties
    tool_name = "basic_net_update"
    init.global_init("tool", "int", tool_name, sys.argv, execution_timeout=2000)
    # Process command line arguments
    try:
        arguments = docopt(__doc__)
    except SystemExit as e:
        # If there is a message that means we had invalid arguments
        if e.message:
            log.logger.info("{0}".format(e.message))
            exception.handle_invalid_argument()
        # Otherwise it is a call to help text
        else:
            raise
    rc = 0
    path = None
    try:
        path = get_internal_file_path_for_import("lib", "nrm_default_configurations", "basic_network.py").strip()
        shutil.copy2(path, "backup.py")  # Makes a copy as backup
        if arguments['PROFILES']:
            categories = arguments['PROFILES'].split(",")
            categories = validate_arguments(categories)
            # Increments all the profiles listed
            for category in categories:
                increment_category(category.upper(), path, inc_unsupported=arguments['--inc-all'])
        else:
            # Increments all profiles
            increment_all(path, inc_unsupported=arguments['--inc-all'])
        os.remove("backup.py")  # Removing the backup

    except IOError as e:
        rc = 1
        log.logger.error("Error during copy")
        exception.handle_exception(tool_name, msg=str(e))
    except Exception as e:
        rc = 1
        # Restores the file to pre-edit state
        shutil.move("backup.py", path)
        log.logger.error("Error occurred and backup restored")
        exception.handle_exception(tool_name, msg=str(e))

    init.exit(rc)


if __name__ == '__main__':
    cli()     # pragma: no cover
