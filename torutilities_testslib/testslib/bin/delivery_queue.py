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
# Name    : delivery_queue
# Purpose : Tool to administer the automation of rpm delivery
# Team    : Blade Runners
# ********************************************************************

"""
delivery queue - Tool to administer the automation of rpm delivery

Usage:
  delivery_queue deliver USERNAME RPM [ENM_DROP]
  delivery_queue view_jiras USERNAME RPM [-v | --valid] [--verbose]

Arguments:
   USERNAME         Is the signum for the user
   RPM              RPM to be delivered in format: 50.1.1
   ENM_DROP         ENM Drop to deliver the rpm (17.13, 17.14....so on)

Options:
   -v, --valid      View only the valid JIRAS
   --verbose        Output the jira list in verbose mode, including the available commit message

Examples:
    ./delivery_queue deliver eaaaaaa 51.1.1
        Deliver the last built rpm without specifying the ENM Drop queue

    ./delivery_queue deliver eaaaaaa 51.1.1 17.13
        Deliver the last built rpm to the specified ENM Drop queue

    ./delivery_queue view_jiras eaaaaaa
        View the jiras included in the last rpm build

"""
import sys
import signal
import getpass

from docopt import docopt
from packaging import version as packaging_version

from testslib import delivery_queue
from enmutils.lib import log, init, exception


def _sprint_validate(rpm, username, password):
    """
    Determine if the rpm can be correctly delivered to queue

    :param rpm: Rpm version to be checked
    :type rpm: str
    :param username: User who will login into the FEM
    :type username: str
    :param password: Password of the user who will login into the FEM
    :type password: str

    :return: Boolean indicating if the rpm can be delivered or not
    :rtype: bool
    """
    current_drop = delivery_queue.get_enm_drop()
    last_delivered, drop = delivery_queue.get_last_delivered_rpm(rpm=rpm, username=username, password=password)[0]
    last_delivered_ver = packaging_version.parse(last_delivered)
    current_rpm_ver = packaging_version.parse(rpm.strip())
    if current_drop > drop or current_rpm_ver > last_delivered_ver:
        return True
    log.logger.info("Cannot deliver rpm {0} to drop {1}, as rpm versions {2}* are linked to drop {3}.\nPlease "
                    "deliver an incremented rpm version.".format(rpm, current_drop, last_delivered[:5], drop))
    return False


def _print_last_build_jiras(username, password, rpm, valid=False, verbose=False):
    """
    Outputs the list of jiras which can be included in a delivery

    :param username: User who will login into the FEM
    :type username: str
    :param password: Password of the user who will login into the FEM
    :type password: str
    :param rpm: Rpm version to be checked
    :type rpm: str
    :param valid: Flag allowing the end user to ignore unsupported jiras
    :type valid: bool
    :param verbose: Boolean indicating if the full valid ticket details should be returned.
    :type verbose: bool
    """
    queue = delivery_queue.CIFWKSession(username, password, rpm_version=rpm)
    if verbose:
        result = queue.get_jira_details_for_email()
    elif not valid:
        all_jiras = []
        for build in queue.builds:
            all_jiras.extend(delivery_queue.get_rpm_build_jira(build_num=str(build)))
        result = all_jiras
    else:
        result = queue.get_jiras_for_jenkins_build()
    if not result:
        log.logger.info("Last undelivered rpm(s) contains no valid jira tickets.")
        return
    log.logger.info("Last undelivered rpm(s) contains the following jira tickets:")
    log.logger.info("\n".join(result))


def cli():
    # Register signal handler
    signal.signal(signal.SIGINT, init.signal_handler)

    # Initialize logging and load our configuration properties
    tool_name = "delivery_queue"
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

    rc = 1
    try:
        success = False
        password = getpass.getpass("Password is required to proceed: ")
        if arguments['deliver']:
            if _sprint_validate(arguments['RPM'], arguments['USERNAME'], password):
                queue = delivery_queue.CIFWKSession(arguments['USERNAME'], password, rpm_version=arguments['RPM'],
                                                    enm_drop=arguments['ENM_DROP'])
                queue.open_session()
                rc = queue.deliver_rpm()
                if rc:
                    log.logger.info("Successfully delivered rpm: {} to ENM Drop: {}".format(queue.rpm_version,
                                                                                            queue.enm_drop))
                    success = True
                else:
                    log.logger.info("Failed to deliver RPM, please check /var/log/enmutils/CIFWKSession.log.")
        elif arguments['view_jiras']:
            _print_last_build_jiras(arguments['USERNAME'], password, arguments['RPM'], arguments['--valid'],
                                    arguments['--verbose'])
            success = True
        if success:
            rc = 0
    except Exception as e:
        exception.handle_exception(tool_name, msg=str(e))

    init.exit(rc)


if __name__ == '__main__':
    cli()
