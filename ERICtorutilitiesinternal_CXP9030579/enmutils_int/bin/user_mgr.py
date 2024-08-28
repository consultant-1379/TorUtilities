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
# **************************************************************************
# Name    : user_mgr
# Purpose : Automation tool for single or bulk creation and deletion of ENM users
# **************************************************************************

"""
user_mgr -  Automation tool for single or bulk creation and deletion of ENM users

Usage:
  user_mgr create USERNAME PASSWORD ROLES [(FIRSTNAME LASTNAME EMAIL)] [RANGE]
  user_mgr create --file CSVFILE PASSWORD
  user_mgr delete (USERNAME [RANGE] | --file CSVFILE)
  user_mgr list [USERNAME] [--limit=<LIMIT>]

Arguments:
   OPERATION        Is one of: 'create', 'delete' or 'list'
   USERNAME         Is the name for the user eg. pmload
   PASSWORD         Is the password for the user eg. Password14 (mandatory if operation is 'create')
   FIRSTNAME        Is the firstname of the user i.e. Joe
   LASTNAME         Is the surname of the user i.e. Bloggs
   EMAIL            Is the user's email i.e. joe.bloggs@ericsson.com
   RANGE            Are integer values, representative of start and end number of users, to perform the selected action upon
   CSVFILE          Is a csv file containing multiple users. See note below for file format (NB: Also, the Password must be supplied on the command line)
   ROLES            Is one or many identity roles to assign to the user (mandatory if operation is 'create')
   --file           Must be supplied with the create and delete operations if we want to create or delete users from a file

Examples:
    ./user_mgr create john Password14 OPERATOR
      Creates a single user with username 'john' and password 'Password14' assigning the user to the 'OPERATOR' role

    ./user_mgr create john Password14 ADMINISTRATOR,OPERATOR
      Creates a single user with username 'john' and password 'Password14' assigning the user to the 'ADMINISTRATOR' and 'OPERATOR' roles

    ./user_mgr create john Password14 OPERATOR 1-10
      Creates a 10 users with username 'john1' to 'john10' and password 'Password14' assigning the user to the 'OPERATOR' role

    ./user_mgr create joe_bloggs Password14 ADMINISTRATOR,OPERATOR Joe Bloggs joe.bloggs@ericsson.com
      Creates a single user with username 'joe_bloggs', firstname 'Joe', lastname 'Bloggs' and email 'joe.bloggs@ericsson.com'

    ./user_mgr create --file enm_users.csv Password14
      Creates the users in the enm_users.csv file. Password must be supplied on command line. Note the use of the --file argument, which is mandatory

    ./user_mgr delete --file /var/tmp/enm_users.csv
      Deletes the users in the enm_users.csv file. The --file argument is mandatory when a file of users is supplied on the command line.

    ./user_mgr delete john
      Deletes a single user with username 'john'

    ./user_mgr list
      Lists all users and their roles

    ./user_mgr list pmload
      Lists all users and their roles that have usernames that start with 'pmload'
      Please note the number of results returned with roles is limited to 100 as anymore would have an impact on the system
      To override this functionality add --force to your command#

    ./user_mgr list pmload --limit=all
      Lists all users and their roles that have usernames that start with 'pmload'
      This command will return all users and their assigned roles.
      Please note this can have an impact on system performance with large numbers of users.

NOTE:
    The username and password must adhere to OpenIDM policy standards
    Roles are case sensitive, this should be a comma-delimited list of roles (both on the command line, and in the CSV file)

    N.B. CSV File example:
    USERNAME,FIRSTNAME,LASTNAME,EMAIL,ROLES
    enm_user1,joe,bloggs,joe.bloggs@ericsson.com,ADMINISTRATOR,OPERATOR
    enm_user2,jane,doe,jane.doe@ericsson.com,ADMINISTRATOR

    CSV File Notes:
    1. There must be no spaces between fields in the file
    2. Roles are supplied at the end of each line, and are comma separated

Options:
  -h        Print this help text
"""

import sys
import csv
import signal

from enmutils.lib import enm_user_2 as enm_user
from enmutils.lib import (log, init, exception, arguments, timestamp)
from enmutils_int.lib.enm_user import get_workload_admin_user

from docopt import docopt
from tabulate import tabulate
from requests.exceptions import HTTPError


def list_users(prefix=None, limit=None):
    """
    Lists all ENM usernames and their corresponding roles

    :type prefix: string
    :param prefix: Optional filter to only print usernames beginning with this prefix
    :type limit: string or int
    :param limit: Accept string = all else get int or default to limit = 100

    """

    tabulate_data = []

    if not limit:
        limit = 100
    elif limit.isdigit():
        log.logger.debug("Limiting roles output to: {0}".format(limit))
        limit = int(limit)
    elif limit != "all":
        log.logger.info(log.red_text("Please enter a valid number or 'all' argument. '{0}' is not a valid option for limit.".format(limit)))
        return

    msg = "USERS"
    if prefix is not None:
        msg = "{0} WITH PREFIX {1}".format(msg, prefix)

    usernames = enm_user.User.get_usernames(user=get_workload_admin_user())

    log.logger.info(log.purple_text("".join(["-" for _ in range(0, len(msg))])))
    log.logger.info(log.purple_text(msg))
    log.logger.info(log.purple_text("".join(["-" for _ in range(0, len(msg))])))
    # The result attribute should contain a list of dicts containing data for each user
    rest_requests = 1

    for username in sorted(usernames):
        privileges = None
        if not prefix or username.startswith(prefix):
            if limit == "all" or rest_requests <= limit:
                privileges = enm_user.get_user_privileges(username, user=get_workload_admin_user())
            user_info = [log.green_text(username), log.cyan_text(",".join([i.name for i in privileges]) if privileges else "-")]
            tabulate_data.append(user_info)
            rest_requests += 1

    log.logger.info(
        tabulate(
            sorted(tabulate_data),
            headers=[
                log.blue_text('Username'),
                log.blue_text('Roles')]))

    log.logger.info(log.purple_text("".join(["-" for _ in range(0, len(msg))])))
    if rest_requests >= limit if isinstance(limit, int) else False:
        log.logger.info(log.red_text("*** Exceeded role request limit of {0}. Run with user_mgr list <OPTION> --limit=all to get all roles ***\n"
                                     "*** Please note running with --limit=all can have an impact on system performance if there are a large number of users ***".format(limit)))
    log.logger.info(log.purple_text("NUMBER OF USERS LISTED: {0}/{1}".format(len(tabulate_data), len(usernames))))
    log.logger.info(log.purple_text("".join(["-" for _ in range(0, len(msg))])))


def create_users_with_username_and_password(username, password, roles, first_name=None, last_name=None, email=None,
                                            range_start=None, range_end=None):
    """
    Creates users with provided username, password and roles

    :type username: string
    :param username: name of user we want to create
    :type password: string
    :param password: password for user we want to create
    :type roles: list
    :param roles: list of roles we want to assign to user
    :type first_name: str
    :param first_name: first name we want to assign to user
    :type last_name: str
    :param last_name: last name we want to assign to user
    :type email: str
    :param email: email we want to assign to user
    :type range_start: int
    :param range_start: the number from which we want to start creating users
    :type range_end: int
    :param range_end: the number from which we want to start creating users

    :rtype: bool
    :returns: boolean indicating whether create for all valid users was successful or not
    """
    users = []
    if range_start:
        for i in xrange(range_start, range_end + 1):
            users.append(enm_user.User("{0}{1}".format(username, i), password, roles=roles, keep_password=True))
    else:
        users.append(enm_user.User(username, password, first_name=first_name, last_name=last_name, email=email,
                                   roles=roles, keep_password=True))
    users = _remove_users_with_invalid_usernames(users, expected=False)
    users = _remove_users_with_invalid_roles(users)
    return _execute(users, "create")


def create_users_with_file(file, password):  # pylint: disable=redefined-builtin
    """
    Creates users defined in a csv file

    :type file: string
    :param file: path to file which contains users we want to created
    :type password: string
    :param password: password we want to use for the users specified in the file

    :rtype: bool
    :returns: boolean indicating whether create for all valid users was successful or not
    """
    users = _parser_users_from_file(file, "create", password=password)
    users = _remove_users_with_invalid_usernames(users, expected=False)
    users = _remove_users_with_invalid_roles(users)
    return _execute(users, "create")


def delete_users_with_username(username, range_start=None, range_end=None):
    """
    Deletes users with given username on ENM

    :type username: string
    :param username: name of user we want to delete on ENM
    :type range_start: int
    :param range_start: the number from which we want to start deleting users
    :type range_end: int
    :param range_end: the number from which we want to start deleting users

    :rtype: bool
    :returns: boolean indicating whether delete for all valid users was successful or not
    """
    users = []
    if range_start:
        for i in xrange(range_start, range_end + 1):
            users.append(enm_user.User("{0}{1}".format(username, i), "UNUSED PASSWORD"))
    else:
        users.append(enm_user.User(username, "UNUSED PASSWORD"))
    users = _remove_users_with_invalid_usernames(users, expected=True)
    return _execute(users, "delete")


def delete_users_with_file(file):  # pylint: disable=redefined-builtin
    """
    Deletes users with given username on ENM

    :type file: string
    :param file:  path to file which contains users we want to delete

    :rtype: bool
    :returns: boolean indicating whether delete for all valid users was successful or not
    """
    users = _parser_users_from_file(file, "delete")
    users = _remove_users_with_invalid_usernames(users, expected=True)
    return _execute(users, "delete")


def _remove_users_with_invalid_usernames(users, expected=True):
    """
    Removes users with invalid usernames from the list of users provided

    :type users: list
    :param users: list of users (enm_user.User) we want to check for invalid usernames
    :type expected: bool
    :param expected: flags whether we expect the users provided to already exist on enm or not

    :rtype: users
    :returns: list of enm_user.User objects all of which have valid usernames for the operation we want to perform
    """
    usernames = enm_user.User.get_usernames(get_workload_admin_user())
    invalid_users = ([user.username for user in users if user.username not in usernames] if expected
                     else [user.username for user in users if user.username in usernames])
    if invalid_users:
        log.logger.warn("Not attempting operation on users {0} as they are {1} on the system"
                        "".format(",".join(invalid_users), "not" if expected else "already"))
        return [user for user in users if user.username not in invalid_users]
    return users


def _remove_users_with_invalid_roles(users):
    """
    Removes users with invalid roles from the list of users provided

    :type users: list
    :param users:  users to remove with invalid roles

    :rtype: list
    :returns: list of enm_user.User objects all of which have valid roles
    """
    role_names = enm_user.EnmRole.get_all_role_names()
    invalid_users = []
    invalid_roles = []
    for user in users:
        for role in user.roles:
            if role.name not in role_names:
                invalid_roles.append(role.name)
                invalid_users.append(user.username)
    if invalid_users:
        log.logger.warn("Not attempting operation on users {0} as they have the following invalid roles {1}"
                        "".format(",".join(invalid_users), ",".join(invalid_roles)))
        return [user for user in users if user.username not in invalid_users]
    return users


def _parser_users_from_file(file, operation, password=None):  # pylint: disable=redefined-builtin
    """
    Creates enm.User objects from the information provided in the specified file

    :type file: str
    :param file: path to file which contains users we want to instantiate
    :type operation: str
    :param operation: flags whether we want to create or delete the specified users
    :type password: str
    :param password: password we want users to have upon creation

    :rtype: list
    :returns: list of enm_user.User objects
    """
    users = []
    invalid_lines = []
    header_found = False
    with open(file) as fh:
        for user_info in csv.reader(fh):
            if not user_info:
                continue
            user_info = [field.strip() for field in user_info]

            if not header_found and "roles" in user_info and "email" in user_info:
                header_found = True
                continue

            if "" in user_info or (operation == "create" and len(user_info) < 5):
                invalid_lines.append("".join(user_info))
                continue
            if operation == "create":
                username, firstname, lastname, email = user_info[:4]
                user_roles = user_info[4:]
                users.append(enm_user.User(username, password=password, first_name=firstname, lastname=lastname,
                                           email=email, roles=user_roles))
            else:
                username = user_info[0]
                users.append(enm_user.User(username, "UNUSED PASSWORD"))
    return users


def _execute(users, operation):
    """
    Function that performs the create or delete operation on given users

    :type users: list
    :param users: list of enm.User objects for crud operation to be performed on
    :type operation: string
    :param operation: type of operation we want to perform (van be create or delete)

    :rtype: bool
    :returns: boolean indicating whether operation was successful for all valid users
    """
    num_successful = 0
    crud_function = enm_user.User.create if operation == "create" else enm_user.User.delete
    start_time = timestamp.get_current_time()
    log.logger.info("")
    log.logger.info(log.purple_text("USER MANAGER {0}".format(operation.upper())))
    log.logger.info("")

    if not users:
        log.logger.error("No users to perform {0} operation on. Please try again with valid users...".format(operation))
        log.logger.info("")
        return False

    for user in users:
        msg = "  Attempting to {0} user {1} {2} ....".format(
            operation, log.cyan_text(user.username), "" if operation == "delete" else "with roles {0}".format(
                log.cyan_text(str(user.roles))))
        log.logger.info(msg)
        try:
            crud_function(user)
        except HTTPError as e:
            log.logger.error(str(e))
            continue
        num_successful += 1
        log.logger.info("  Successfully completed {0} operation for user {1} ".format(operation, log.cyan_text(user.username)))

    end_time = timestamp.get_current_time()
    duration = timestamp.get_elapsed_time_in_duration_format(start_time, end_time)

    # Print header
    log.logger.info("")
    log.logger.info(log.purple_text("\n{0} SUMMARY".format(operation.upper())))
    log.logger.info(log.purple_text("----------------------"))
    log.logger.info("  USERS {0}D: {1}/{2}".format(operation.upper(), num_successful, len(users)))
    log.logger.info("  EXECUTION TIME: {0}".format(duration))
    log.logger.info("")

    return num_successful == len(users)


def cli():
    """
    B{Name : user_mgr.py
    Purpose : Automation tool for single or bulk creation and deletion of ENM users}
    """

    # Register signal handler
    signal.signal(signal.SIGINT, init.signal_handler)

    # Initialize logging and load configuration properties
    tool_name = "user_mgr"
    init.global_init("tool", "int", tool_name, sys.argv, execution_timeout=0)

    # Process command line arguments
    try:
        argument_dict = docopt(__doc__)
    except SystemExit, e:
        # If there is a message that means we had invalid arguments
        if e.message:
            log.logger.info("\n {0}".format(e.message))
            exception.handle_invalid_argument()
        else:
            # Otherwise it is a call to help text and we are exiting with a SystemExit (rc 0)
            raise
    range_start = range_end = None
    if argument_dict["RANGE"]:
        (range_start, range_end) = arguments.get_numeric_range(argument_dict["RANGE"])
    result = False
    rc = 0
    try:
        get_workload_admin_user()

        if argument_dict["create"]:
            result = create_users_with_username_and_password(argument_dict["USERNAME"], argument_dict["PASSWORD"], argument_dict["ROLES"].split(","),
                                                             argument_dict["FIRSTNAME"], argument_dict["LASTNAME"],
                                                             argument_dict["EMAIL"], range_start=range_start, range_end=range_end) \
                if not argument_dict['--file'] else create_users_with_file(argument_dict["CSVFILE"], argument_dict["PASSWORD"])
        elif argument_dict["delete"]:
            result = delete_users_with_username(argument_dict["USERNAME"], range_start=range_start, range_end=range_end) \
                if not argument_dict['--file'] else delete_users_with_file(argument_dict["CSVFILE"])
        elif argument_dict["list"]:
            if argument_dict["--limit"]:
                list_users(argument_dict["USERNAME"], limit=argument_dict["--limit"])
            else:
                list_users(argument_dict["USERNAME"])
            result = True
    except:
        exception.handle_exception(tool_name)

    if not result:
        rc = 1

    init.exit(rc)


if __name__ == '__main__':  # pragma: no cover
    cli()
