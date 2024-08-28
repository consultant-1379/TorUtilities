#!/usr/bin/env python
import os
import pkgutil
from enmutils.lib import log, filesystem

ENM_SCRIPTING_PATH = pkgutil.get_loader('enmscripting').filename
AUTHENTICATOR_FILE = os.path.join(ENM_SCRIPTING_PATH, 'security', 'authenticator.py')


def add_timeout_to_authenticator_file():
    """
    Updates the authenticator.py file of enm-scripting with a timeout of 5 minutes for logging in to ENM
    Introduced as part of TR RTD-8269
    """
    needs_update = False
    log.log_init()
    if filesystem.does_file_exist(AUTHENTICATOR_FILE):
        log.logger.info("File authenticator.py exists")
        with open(AUTHENTICATOR_FILE, 'r') as auth_file:
            lines = auth_file.read().splitlines()
        for line in lines:
            if 'session.post' in line and 'timeout' not in line:
                pos = lines.index(line)
                new_line = line.rstrip() + ' timeout=300,'
                lines.insert(pos, new_line)
                lines.pop(pos + 1)
                needs_update = True
                break

        if needs_update:
            log.logger.info("File will be updated with a timeout of 300 secs")
            with open(AUTHENTICATOR_FILE, 'w') as auth_file:
                for line in lines:
                    auth_file.write(line + '\n')


def cli():
    """
    Main function
    """
    add_timeout_to_authenticator_file()


if __name__ == "__main__":  # pragma: no cover
    cli()
