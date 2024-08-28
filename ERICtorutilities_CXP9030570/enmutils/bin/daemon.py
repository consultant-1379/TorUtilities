#!/usr/bin/env python
# ********************************************************************
# Ericsson LMI                 Utility Script
# ********************************************************************
#
# (c) Ericsson LMI 2014 - All rights reserved.
#
# The copyright to the computer program(s) herein is the property of Ericsson LMI. The programs may be used
# And/or copied only with the written permission from Ericsson LMI or in accordance with the terms and conditions stipulated
# In the agreement/contract under which the program(s) have been supplied.
#
# ********************************************************************
# Name    : daemon
# Purpose : Tool that runs code as a background daemon
# Team    : Blade Runners
# ********************************************************************

"""
daemon - Tool that runs code as a background daemon

Usage:
  daemon IDENTIFIER [LOG_IDENTIFIER]

Arguments:
   IDENTIFIER        Is the identifier
   LOG_IDENTIFIER    Is the log identifier to use for log folder name

Examples:
    ./daemon pm_06
        Will run anything associated with pm_06 identifier which is stored in redis

Options:
  -h        Print this help text
"""

import os
import sys

from docopt import docopt

from enmutils.lib import (init, exception, config, persistence, log)


def cli():

    # Process command line arguments
    try:
        arguments = docopt(__doc__)
    except SystemExit, e:
        # If there is a message that means we had invalid arguments
        if e.message:
            print e.message
            sys.exit(1)
        # Otherwise it is a call to help text
        else:
            raise

    identifier = arguments['IDENTIFIER']
    log_identifier = arguments['LOG_IDENTIFIER']

    # Initialize logging and load our configuration properties
    init.global_init("tool", "prod", log_identifier or identifier, sys.argv,
                     simplified_logging=True, execution_timeout=-1)

    # Attempt to load internal props in case our target is in enmutils_int
    try:
        config.load_config("int", True)
    except:
        pass

    # Attempt to load the function reference and arguments from persisted target
    pickled_identifier = identifier + '_pickled'
    target = persistence.get(pickled_identifier)
    if target:
        persistence.remove(pickled_identifier)

    if target is None:
        exception.handle_invalid_argument("No pickled data file for identifier {0}".format(identifier))

    # Check that we got a list with 2 elements
    if not isinstance(target, list) or len(target) != 2:
        exception.handle_invalid_argument("Pickled data for identifier %s is not correctly formatted" % identifier)

    # Pull the function reference and arguments from the target tuple
    func = target[0]
    args = target[1] or []
    rc = 0
    result = None

    # Execute the function
    try:
        # Attempt to load the module
        __import__(func.__module__, globals())
        result = func(*args)
    except:
        exception.process_exception("{0} (daemon)".format(identifier))
        rc = 5
    finally:
        try:
            daemon_dir = "/var/tmp/enmutils/daemon"
            os.remove(
                os.path.abspath(os.path.realpath(os.path.join(daemon_dir, "%s.pid" % identifier))))
        except OSError:
            log.logger.debug('WARNING: Pid file for "%s" does not exist. Not deleting it.' % identifier)

    if result is not None and not result:
        rc = 1

    init.exit(rc)


if __name__ == "__main__":
    cli()
