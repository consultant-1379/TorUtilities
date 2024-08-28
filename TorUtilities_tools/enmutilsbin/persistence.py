#!/usr/bin/env python
# ********************************************************************
# Ericsson LMI                 Utility Script
# ********************************************************************
#
# (c) Ericsson LMI 2017 - All rights reserved.
#
# The copyright to the computer program(s) herein is the property of Ericsson LMI. The programs may be used
# And/or copied only with the written permission from Ericsson LMI or in accordance with the terms and conditions stipulated
# In the agreement/contract under which the program(s) have been supplied.
#
# ********************************************************************
# Name    : persistence
# Purpose : Script that clears all non-infinite persisted keys from the persistence.db database file.
#           This script is intended to be executed after an rpm install/upgrade of the utilities package to clear
#           any stale persisted data, or in the case of a major configuration change to the system.
# Team    : Blade Runners
# ********************************************************************

"""
persistence - Tool for management of and interaction with the ENM Utilities persistence(database) store

Usage:
  persistence backup
  persistence clear [force] [--index=<index>] [--auto-confirm]
  persistence list [TOKEN]  [--index=<index>]
  persistence get KEY [--index=<index>] [--detailed] [--json]
  persistence set KEY VALUE EXPIRY [--index=<index>]
  persistence remove KEY [--index=<index>] [--force]
  persistence restore

Arguments:
  TOKEN           Token to search for in DB; all keys containing the TOKEN will be listed (optional)
  KEY             Key name to use when getting or setting a value
  VALUE           Value to set with the corresponding key
  force           This will remove all keys including those persisted indefinitely
  EXPIRY          Time in integer seconds for the value to persist in the store before it is dropped.
                  Argument INDEFINITE (or indefinite) will persist the key permanently
  --index=<index> Numerical index to use when querying the persistence - The value must be in range from 0 to 999
  --force         Optional flag to force the removal of a key from persistence
  --auto-confirm  Automatic confirmation, when force clearing the production persistence
  --detailed      Returns the detailed contents of the persisted object
  --json          Returns content in json format

Examples:
    ./persistence clear
        Clears all the keys from the database that were persisted for a specified time, it does not clear those keys
        persisted indefinitely.

    ./persistence clear force
        Clears all the keys from the database including those persisted indefinitely.

    ./persistence list
        Lists all the keys in the database.

    ./persistence list enm
        Lists all the keys containing the TOKEN enm in the database.

    ./persistence get enm_utilities
        Gets the value of the key enm_utilities from the database.

    ./persistence set enm_utilities some_value 2154
        Sets the key enm_utilities with an expiry time of 2154 seconds in the database.

    ./persistence set enm_utilities some_value INDEFINITE
        Sets the key enm_utilities with no expiry time in the database.

    ./persistence remove enm_utilities
        Removes the key enm_utilities from the database.

    ./persistence backup
        Backup the in memory Redis DB to disk. This overwrites any old backup stored in this directory.
        Only one backup is kept at a time in /var/db/enmutils/backup

    ./persistence restore
        Restore from disk the Redis DB saved by a backup

Options:
  -h        Print this help text

Note:
  Using special characters in the value of arguments KEY, VALUE and TOKEN is generally allowed, but to be safe and avoid
  unwanted shell globbing, it is recommended to surround the value with single quotes.

  The value of argument TOKEN cannot start with a dash character "-"
"""

import json
import os
import pprint
import sys
import time

from docopt import docopt

from enmutils.lib import exception, filesystem, init, log, persistence
from enmutils.lib.custom_json_encoder import CustomEncoder
from enmutils.lib.enm_node import Node


def list(token, db):  # pylint: disable=redefined-builtin
    """
    List all keys in the persistence store that contain the specified token in the key name

    :param: token: Token to search for in all key names
    :type: token: str
    :param: db: Persistence to use to perform query
    :type: db: enmutils.lib.Persistence object

    :returns: true
    :rtype: bool

    """

    all_keys = db.get_all_keys()

    if len(all_keys) > 0:
        for key in all_keys:
            if token in key:
                log.logger.info(key)
    else:
        log.logger.warn("No keys in the persistence store")

    return True


def log_in_json_format(value):
    """
    Logs the persistence value in json format
    :param: value: persistence value
    :type: value: enmutils.lib.Persistence object
    """
    data = None
    if hasattr(value, '__dict__'):
        data = json.dumps(value.__dict__, cls=CustomEncoder)
    else:
        data = json.dumps(value, cls=CustomEncoder)
    log.logger.info(data)


def get(key, db, detailed=False, json_formatted=False):
    """
    Print the value of the specified key

    :param key: Name of the key to fetch and print
    :type key: str
    :param db: Persistence to use to perform query
    :type db: enmutils.lib.Persistence object
    :param detailed: Boolean indicating if the __dict__ of the key should be logged
    :type detailed: bool
    :param json_formatted: Boolean indicating if json formatted output should be logged
    :type json_formatted: bool

    :returns: value of the specified key
    :rtype: string

    """

    value = None

    if db.has_key(key):
        value = db.get(key)
    if value is None:
        log.logger.info(log.yellow_text("Key {0} was not found in the persistence store".format(key)))
    elif json_formatted:
        log_in_json_format(value)
    elif detailed and hasattr(value, '__dict__'):
        log.logger.info("{0}".format(pprint.pformat(value.__dict__)))
    else:
        log.logger.info("{0} = {1}".format(key, value))

    return value is not None


def set(key, value, expiry, db):  # pylint: disable=redefined-builtin
    """
    Sets the key-value pair in the persistence store

    :param: key: Name of the key to set
    :type: key: str
    :param: value: The value associated with the key
    :type: value: str
    :param: expiry: The duration for which the key-value pair should remain in the store; after the expiration duration, the key-value pair will be silently dropped
    :type: expiry: int
    :param: db: Persistence to use to perform query
    :type: db: enmutils.lib.Persistence object

    :returns: whether the database has the specified key
    :rtype: bool

    """

    db.set(key, value, int(expiry))

    return db.has_key(key)


def remove(key, db, force=False):
    """
    Removes the specified key from the persistence store

    :param key: Name of the key to remove
    :type key: str
    :param db: Persistence to use to perform query
    :type db: enmutils.lib.Persistence object
    :type force: bool
    :param force: Option to override the check for profiles still allocated to nodes

    :returns: whether the database has the specified key
    :rtype: bool

    """
    if not force and db.has_key(key):
        item = db.get(key)
        if isinstance(item, Node) and hasattr(item, 'profiles') and item.profiles:
            log.logger.error("Cannot remove node while profile(s): {0} are still allocated."
                             .format(item.profiles))
            return False
    db.remove(key)

    return not db.has_key(key)


def _log_result(result, arguments):
    """
    Logs operation on database persistence, can either be set or remove

    :param result: return code
    :type result: int
    :param arguments: contains either 'set' or 'remove'
    :type arguments: dict

    """
    outcome = "successful" if result else "unsuccessful"

    if arguments["set"]:
        log.logger.info("For operation SET,  result was {0} for persisting '{1}' with value '{2}' to database".format(outcome, arguments["KEY"], arguments["VALUE"]))

    elif arguments["remove"]:
        log.logger.info("For operation REMOVE,  result was {0} for removing '{1}' from database".format(outcome, arguments["KEY"]))


class RedisVariablesMixin(object):
    """
    RedisVariablesMixin: Object which holds common variables for backup and restore Objects
    """
    default_db_backup_name = "enmutils.db"
    default_db_filesystem_path = "/var/db/enmutils/"
    custom_db_backup_path = "{0}backup/".format(default_db_filesystem_path)


class BackupDb(RedisVariablesMixin):
    def __init__(self):
        """
        BackupDb: Creates a backup of the Redis db and saves it too the backup directory.
        This will overwrite any other backups currently stored in this directory.

        """
        super(BackupDb, self).__init__()
        filesystem.remove_dir(self.custom_db_backup_path)  # Remove old backups
        filesystem.create_dir(self.custom_db_backup_path)  # Create directory for backup

    def execute(self):
        persistence.save()
        filesystem.copy("{0}{1}".format(self.default_db_filesystem_path, self.default_db_backup_name),
                        "{0}{1}_backup.db".format(self.custom_db_backup_path, time.strftime("%Y%m%d-%H%M%S")))
        log.logger.info(log.green_text("Backup of persistence taken. Stored in: {0}".format(
            log.blue_text(self.custom_db_backup_path))))


class RestoreDb(RedisVariablesMixin):
    def __init__(self):
        """
        RestoreDb: Restores backup of Redis db from the backup directory if it exists

        """
        super(RestoreDb, self).__init__()

    def execute(self):
        if os.path.isdir(self.custom_db_backup_path) and os.listdir(self.custom_db_backup_path):
            backup_file_name = os.listdir(self.custom_db_backup_path)[0]
            persistence.shutdown()
            log.logger.info(log.green_text("Redis has been shut down."))
            filesystem.copy("{0}{1}".format(self.custom_db_backup_path, backup_file_name),
                            "{0}{1}".format(self.default_db_filesystem_path, self.default_db_backup_name))

            persistence.default_db()  # Re-initialise redis process after shutdown
            log.logger.info(log.green_text("Re-initialising Redis with data from backup: {0}".format(
                log.blue_text(self.custom_db_backup_path + backup_file_name))))
        else:
            log.logger.error("There is no backup file in the backup directory. Unable to do a restore.")


def cli():
    tool_name = "persistence"
    init.global_init("tool", "prod", tool_name, sys.argv)

    # Process command line arguments
    try:
        arguments = docopt(__doc__)
    except SystemExit as e:
        # If there is a message that means we had invalid arguments
        if e.message:
            log.logger.info("\n {0}".format(e.message))
            exception.handle_invalid_argument()
        # Otherwise it is a call to help text
        else:
            raise

    parameters = []

    if arguments['--index']:
        try:
            redis_index = int(arguments['--index'])
            if redis_index == -1:
                raise ValueError()
        except ValueError:
            exception.handle_invalid_argument('The index you specified is not valid')

        db = persistence.get_db(redis_index)
    else:
        redis_index = 0
        db = persistence.default_db()

    # Figure out what we want to run and build the function reference and parameters
    if arguments["clear"]:
        if arguments["force"]:
            if not arguments["--auto-confirm"] and redis_index == 0:
                # Index zero is the production index, under most situations should not be wiped.
                log.logger.info("Please confirm you wish to continue with clearing the redis db index [{0}]?"
                                "\nDo you wish to continue? (Yes | No)\n".format(redis_index))
                answer = raw_input()
                if not answer.lower() in ["yes"]:
                    return
            func = db.clear_all
        else:
            func = db.clear
    elif arguments["list"]:
        func = list
        if arguments["TOKEN"] is not None:
            parameters = [arguments["TOKEN"], db]
        else:
            parameters = ["", db]
    elif arguments["get"]:
        func = get
        parameters = [arguments["KEY"], db, arguments['--detailed'], arguments['--json']]
    elif arguments["set"]:
        func = set
        if arguments["EXPIRY"].lower() == "indefinite":
            arguments["EXPIRY"] = -1
        else:
            try:
                arguments["EXPIRY"] = int(arguments["EXPIRY"])
            except:
                exception.handle_invalid_argument('Persistence EXPIRY value error. EXPIRY argument must be either "indefinite" or an integer identifying the number of seconds to persist this element for.')
        parameters = [arguments["KEY"], arguments["VALUE"], arguments["EXPIRY"], db]
    elif arguments["remove"]:
        key = arguments['KEY']
        force = arguments['--force']
        if not db.has_key(key):
            exception.handle_invalid_argument('Key "%s" does not exist in the database' % key)
        func = remove
        parameters = [key, db, force]
    elif arguments["backup"]:
        func = BackupDb().execute
    elif arguments["restore"]:
        func = RestoreDb().execute
    rc = 1

    try:
        rc = func(*parameters)
        _log_result(rc, arguments)
    except Exception:
        exception.handle_exception(tool_name)

    if rc is True or (rc is None and func == db.clear):
        rc = 0
    else:
        rc = 1

    init.exit(rc)


if __name__ == '__main__':
    cli()
