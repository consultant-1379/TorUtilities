#!/usr/bin/env python
# ********************************************************************
# Ericsson LMI                 Utility Script
# ********************************************************************
#
# (c) Ericsson LMI 2014 - All rights reserved.
#
# The copyright to the computer program(s) herein is the property of Ericsson LMI. The programs may be used
# and/or copied only with the written permission from Ericsson LMI or in accordance with the terms and conditions stipulated
# in the agreement/contract under which the program(s) have been supplied.
#
# ********************************************************************
# Name    : cli_app
# Purpose : Script that allows users to send cli commands from the command line and view the response
# Team    : Blade Runners
# ********************************************************************

"""
cli_app - Command line tool that takes a single CM CLI command argument, executes it via script engine, and prints the output identical to CLI editor application

Usage:
  cli_app COMMAND [FILE] [--save=IDENTIFIER] [--outfile=PATH] [--debug]
  cli_app --list [--debug]
  cli_app -s IDENTIFIER [FILE] [--debug]

Arguments:
  COMMAND              Is the full command as entered into the CLI editor surrounded in single quotes. Use double quotes within the command if quotes are required
  FILE                 [OPTIONAL] Path to the file to attach to the command

Options:
  -s IDENTIFIER        Used to look up in saved searches
  --list               List all the saved searches
  --save=IDENTIFIER    [OPTIONAL] Identifier to be used to save this command
  --outfile=PATH       [OPTIONAL] File name to use to save the file from the enm response
  --debug              [OPTIONAL] Enables enmscripting debug logging to a log file

Examples:
    ./cli_app 'ap status -n Dublin1'
     Sends an ap command to the cli editor to check the integration status of a node

    ./cli_app 'cmedit get * MeContext'
     Sends a cmedit command to the cli editor to get all managed object instances of type MeContext

    ./cli_app 'cmedit get MeContext=LTE01ERBS00101'
     Sends a cmedit command to the cli editor to get attributes for a particular MeContext instance

    ./cli_app 'shm import -s file:test' /tmp/test
     Sends a shm import command with a file

    ./cli_app 'cmedit get * MeContext' --save cmedit_get
     Saves the given command with 'cmedit_get' identifier

    ./cli_app -s cmedit_get
     Finds cmedit_get in saved searches and execute the corresponding command

    ./cli_app --list
     Lists all the saved searches

    Specific log files for this tool can be found under '/var/log/enmutils/'

Options:
  -h        Print this help text
"""

import base64
import datetime
import getpass
import os
import re
import signal
import sys
import time
import logging
import traceback

import enmscripting
from enmscripting.exceptions import SessionTimeoutException

from docopt import docopt

from enmutils.lib import (init, log, mutexer, persistence, cache)

SAVE_PERSISTENCE_KEY = 'cli_saved_searches'
ENM_ADMIN_CREDS_FILE = "/tmp/enmutils/enm-credentials"
INITIAL_PROMPT = "\nPlease enter the credentials of the ENM account to use"
USERNAME_PROMPT = "Username: "
PASSWORD_PROMPT = "Password: "
FILES_DIR = '/tmp/enmutils'
WORKLOAD_ADMIN_SESSION_KEY = 'workload_admin_session'
ADMINISTRATOR_SESSION_KEY = 'administrator_session'

TOOL_NAME = 'cli_app'
LOG_DIR = "/var/log/enmutils"
RED_TEXT_COLOUR = '\033[91m'
NORMAL_TEXT = '\033[0m'
GREEN_TEXT_COLOUR = '\033[92m'


def handle_invalid_argument(msg=None):
    """
    Exception handler for tools when invalid arguments are supplied

    NOTE: This function should only be invoked by top-level tools, never directly by API modules

    :type msg: str
    :param msg: Custom message to be printed to the user
    """

    # If a custom message is given print it
    log.logger.error("\nERROR: Command line argument validation has failed.")
    if msg is not None:
        log.logger.error("  " + msg)
    else:
        log.logger.error("  Invalid command line arguments")

    log.logger.error(" Please run the tool with '-h' or '--help' for more information about command line arguments and "
                     "supported values.\n")

    init.exit(2)


def check_log_dir():
    """
    Check that log dir exists (create if missing)
    """
    try:
        if not os.path.exists(LOG_DIR):
            os.mkdir(LOG_DIR)
    except Exception as e:
        raise SystemExit("Problem accessing log dir ({0}): {1}".format(LOG_DIR, e))


def initialize_logger():
    """
    Initialize logging to file and to stdout
    """
    log.logger = logging.getLogger('enmscripting')
    log.logger.handlers = []
    log.logger.setLevel(logging.DEBUG)

    check_log_dir()

    logfile_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s (PID %(process)d)')
    file_handler = logging.FileHandler('{0}/{1}.log'.format(LOG_DIR, TOOL_NAME))
    file_handler.setFormatter(logfile_formatter)
    file_handler.setLevel(logging.DEBUG)

    stdout_formatter = logging.Formatter('%(message)s')
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(stdout_formatter)
    stdout_handler.setLevel(logging.INFO)

    log.logger.addHandler(file_handler)
    log.logger.addHandler(stdout_handler)


class NoOuputFromScriptEngineResponseError(Exception):
    error_message = "No output from script engine response"

    def __init__(self, msg, response):
        self.response = response
        super(NoOuputFromScriptEngineResponseError, self).__init__(msg)


def prompt_for_credentials():
    """
    Prompts the operator for the username and password of an ENM user account with the SECURITY_ADMIN role

    :return: 2-element tuple consisting of (username, password)
    :rtype: tuple
    """

    log.logger.info(INITIAL_PROMPT)
    time.sleep(0.1)
    username = raw_input(USERNAME_PROMPT)
    password = getpass.getpass(PASSWORD_PROMPT)
    return username, password


def get_persisted_admin_user_details():
    """
    Get any available persisted credentials

    :return: Containing any available persisted credentials
    :rtype: tuple
    """
    user = persistence.get(WORKLOAD_ADMIN_SESSION_KEY) or persistence.get(ADMINISTRATOR_SESSION_KEY)
    username, password = None, None
    if user:
        username = getattr(user, 'username', None)
        log.logger.debug("Persisted username: [{0}]".format(username))
        password = (base64.b64decode(getattr(user, 'password', None)) if "workload" in username else
                    getattr(user, 'password', None))
    return username, password


def get_credentials():
    """
    Get the available user credentials on the deployment or prompt for credentials

    :return: Tuple containing the credentials
    :rtype: tuple
    """
    username, password = get_persisted_admin_user_details()
    if not all([username, password]):
        if not os.path.isfile(ENM_ADMIN_CREDS_FILE):
            username, password = prompt_for_credentials()
        else:
            with open(ENM_ADMIN_CREDS_FILE, 'r') as f:
                log.logger.debug("Attempting to read credentials from file: [{0}]".format(ENM_ADMIN_CREDS_FILE))
                lines = f.readlines()
                if lines and len(lines) >= 2:
                    username = lines[0].strip()
                    password = lines[1].strip()
                else:
                    log.logger.warn("Unable to retrieve credentials from: {0}, please ensure the file is created "
                                    "correctly.".format(ENM_ADMIN_CREDS_FILE))
                    username, password = prompt_for_credentials()

    return username, password


def open_enm_scripting_session(url=None, username=None, password=None):
    """
    Creates the ENM session instance

    :param url: ENM url to use to open the session
    :type url: str
    :param username: User who will open the ENM session
    :type username: str
    :param password: Password of the user who will open the ENM session
    :type password: str

    :return: Tuple containing the created session and related values
    :rtype: tuple
    """
    url = cache.get_apache_url() if not url else url
    if not all([username, password]):
        username, password = get_credentials()
    log.logger.debug("Attempting to open ENM scripting session.")
    session = enmscripting.open(url, username, password)
    log.logger.debug("Successfully opened ENM scripting session.")
    return session, url, username, password


def close_file_and_close_session(file_obj, username, session):
    """
    Closes open resources related to the command execution

    :param file_obj: file object
    :type file_obj: BinaryIO
    :param username: Name of the user who executed the command
    :type username: str
    :param session: ENMScripting session instance
    :type session: `requests.Session`
    """
    if file_obj:
        file_obj.close()
    if session:
        log.logger.debug('Closing enm scripting session for {0}'.format(username))
        enmscripting.close(session)
        log.logger.debug("Successfully closed ENM scripting session.")


def _execute_cli_command(cli_command, file_path, outfile_path=None):
    """
    Attempts to run the command specified and prints the output of that command

    :param cli_command: cli command to execute
    :type cli_command: str
    :param file_path: path to file we want to use with cli_command
    :type file_path: str
    :param outfile_path: Path of the output file to be used to save the file in the response
    :type outfile_path: str
    """
    response = enm_execute(cli_command, file_path, outfile_path)
    response_output = response.get_output()
    if len(response_output) > 0:
        for line in response_output:
            if line:
                log.logger.info(line)
    else:
        log.logger.error("ERROR: No result was returned from ENM script-engine service, response:\t{}"
                         .format(response_output))


def enm_execute(command, file_in=None, outfile=None):
    """
    Builds the basic command before calling execute_cmd

    :param command: Command to be executed in ENM
    :type command: str
    :param file_in: Path to the file to be uploaded as part of the command
    :type file_in: str
    :param outfile: Path for downloaded file(s) to be saved too.
    :type outfile: str

    :raises OSError: raised if the supplied file path is not a file
    :raises Exception: raised if the command execution or file download fails.
    :raises NoOuputFromScriptEngineResponseError: raised if there is no output from the command.

    :return: ENM Response object
    :rtype: `TerminalOutput`
    """
    if file_in and not os.path.isfile(file_in):
        raise OSError('File "{0}" does not exist'.format(file_in))
    session, url, username, password = open_enm_scripting_session()
    file_obj = None
    kwargs = {}
    if file_in:
        file_obj = kwargs['file'] = open(file_in, 'rb')
    mod_cmd = None
    if 'password' in command:
        mod_cmd = re.sub(r"password\s+\S+", "password ********", command)
    try:
        response = execute_cmd(session, url, username, password, command, **kwargs)
        if outfile and response.has_files():
            for enm_file in response.files():
                outfile_path = outfile or os.path.join(FILES_DIR, enm_file.get_name())
                log.logger.info("Starting download of file: {0}".format(outfile_path))
                enm_file.download(outfile_path)
            log.logger.info('Downloaded file: {0}'.format(outfile_path))
    except Exception:
        log.logger.debug("Failed while executing ScriptEngine command '{0}' with file '{1}' "
                         .format(mod_cmd[:1000] if mod_cmd else command[:1000], file_in))
        raise
    finally:
        close_file_and_close_session(file_obj, username, session)

    response.command = command
    if not response.is_command_result_available():
        raise NoOuputFromScriptEngineResponseError("No output to parse from ScriptEngineCommand {0}".format(
            command[:1000]), response=response)

    return response


def execute_cmd(session, url, username, password, cmd, **kwargs):
    """
    Executes the supplied command via the ENM scripting session

    :param session: ENM Session instance
    :type session: `request.Session`
    :param url: ENM url to be used in the session
    :type url: str
    :param username: User who will perform the ENM command execution
    :type username: str
    :param password: Password of the user who will perform the ENM command execution
    :type password: str
    :param cmd: Command to be executed in ENM
    :type cmd: str
    :param kwargs: Dictionary of additional key word arguments if any
    :type kwargs: dict

    :raises SessionTimeoutException: raised the ENM Session is no longer available
    :raises Exception: raised if exception does not meet session retry criteria

    :return: ENM Response object
    :rtype: `TerminalOutput`
    """
    wait_time = 5
    max_tries = 3
    for i in range(max_tries + 1):
        try:
            log.logger.debug('Attempting to execute command: {0}'.format(cmd))
            try:
                log.logger.debug("Executing CM CLI command on ENM")
                response = session.terminal().execute(cmd, timeout_seconds=600, **kwargs)
                log.logger.debug("Command execution on ENM complete")
                return response
            except SessionTimeoutException as e:
                log.logger.debug("Redirected to ENM login. SessionTimeoutException received from enmscripting - "
                                 "Therefore we will try to login again. {0}".format(str(e)))
                open_enm_scripting_session(url, username, password)
                raise
            except Exception as e:
                if "Pool is closed" in e.message:
                    log.logger.error("Closed Pool Error received from enmscripting. Re-Executing ScriptEngine command {0}"
                                     .format(cmd))
                    open_enm_scripting_session(url, username, password)
                    raise SessionTimeoutException(str(e))
                raise
        except SessionTimeoutException as e:
            if i < max_tries:
                time.sleep(wait_time)
                continue
            raise


def _get_saved_search_cmd(identifier):
    """
    Attempts get the command from saved searches, if not there it will return None

    :param identifier: Saved search identifier
    :type identifier: str

    :returns: Saved search command value
    :rtype: str
    """
    command = None

    saved_searches = persistence.get(SAVE_PERSISTENCE_KEY)
    if saved_searches and identifier in saved_searches:
        command = saved_searches[identifier]

    return command


def _save_search_cmd(argument_dict):
    """
    Saves the cmedit command into persistence. If it already exists, user is prompted to confirm it.

    :param argument_dict: docopt dictionary
    :type argument_dict: dict
    """
    persist_saved_search = False
    read_input = ''
    saved_searches = persistence.get(SAVE_PERSISTENCE_KEY) or {}
    if argument_dict['--save'] in saved_searches.keys():
        while read_input.upper() not in ['YES', 'NO']:
            read_input = _read_keyboard_input()
        persist_saved_search = True if read_input.upper() == 'YES' else False
    else:
        persist_saved_search = True
    if persist_saved_search:
        saved_searches[argument_dict['--save']] = argument_dict['COMMAND']
        persistence.set(SAVE_PERSISTENCE_KEY, saved_searches, -1)


def _read_keyboard_input():
    """
    Read text from the keyboard and returns it as a string

    :return: whatever as typed as string
    :rtype: str
    """
    log.logger.warn('\nCommand save identifier already exists. Do you want to overwrite? (yes/no)')
    return str(raw_input())


def does_file_exist(file_path, verbose=True):
    """
    Checks whether a local file exists

    :type file_path: string
    :param file_path: Absolute path of the file to be checked
    :type verbose: bool
    :param verbose: Enable/Disable verbose logging
    :return: result True if file exists else False
    :rtype: boolean
    """
    result = False

    # Some file paths that contain dollar signs will be escaped; we need to remove the backslash
    if file_path:
        file_path = file_path.replace(r"\$", "$")

        if not os.path.exists(os.path.realpath(file_path)):
            if verbose:
                log.logger.debug("File {0} does not exist".format(file_path))
        else:
            result = True
            if verbose:
                log.logger.debug("Verified that file {0} exists".format(file_path))
    return result


def cli():
    # Register signal handler
    signal.signal(signal.SIGINT, init.signal_handler)

    # Initialize logging and load our configuration properties
    init.global_init("tool", "prod", TOOL_NAME, sys.argv)

    error_message = "{}Encountered an unhandled exception while running tool {} [{}] \n{}\n{}"

    # Process command line arguments
    try:
        argument_dict = docopt(__doc__)
    except SystemExit, e:
        # If there is a message that means we had invalid arguments
        if e.message:
            log.logger.info("\n {0}".format(e.message))
            handle_invalid_argument()
        else:
            # Otherwise it is a call to help text and we are exiting with a SystemExit (rc 0)
            raise

    if argument_dict["--debug"]:
        initialize_logger()
        log.logger.info(
            "\n{}Debug logs can be found at {} with process id {} \n{}".format(
                GREEN_TEXT_COLOUR, '{0}/{1}.log'.format(LOG_DIR, TOOL_NAME),
                os.getpid(), NORMAL_TEXT))

    rc = 0
    command = None
    if argument_dict['--list']:
        saved_searches = persistence.get(SAVE_PERSISTENCE_KEY)
        if saved_searches:
            for key, val in saved_searches.items():
                log.logger.info('%s="%s"' % (key, val))
        else:
            log.logger.info('No saved searches')
    elif argument_dict['--save']:
        _save_search_cmd(argument_dict)
    elif argument_dict['-s']:
        command = _get_saved_search_cmd(argument_dict['-s'])
        if not command:  # No saved search found, exit with 2
            log.logger.error('No command found for the identifier "%s"' % argument_dict['-s'])
            rc = 2
    else:
        command = argument_dict['COMMAND']

    if command:
        # Execute the required command
        rc = 1
        try:

            # Allows multiple users to run concurrently
            with mutexer.mutex("cli-app-execute-cli-command", persisted=True):
                if argument_dict['FILE'] and not does_file_exist(argument_dict['FILE']):
                    handle_invalid_argument("File does not exist %s" % argument_dict['FILE'])
                _execute_cli_command(command, argument_dict['FILE'], outfile_path=argument_dict['--outfile'])
                rc = 0
        except Exception as e:
            rc = 5
            current_time = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
            log.logger.error(error_message.format(RED_TEXT_COLOUR, TOOL_NAME, current_time, e, NORMAL_TEXT))
            log.logger.debug(traceback.format_exc())

    init.exit(rc)


if __name__ == '__main__':  # pragma: no cover
    cli()
