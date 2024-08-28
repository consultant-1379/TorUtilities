# ********************************************************************
# Name    : Tool Entry Point Updater
# Summary : When tools are deployed to LMS or workloadVM, each one
#           creates an executable: e.g. /opt/ericsson/enmutils/bin/cli_app
#           To prevent core dumps due to file system being full. The
#           module updates the logic on in each entry point when the rpm
#           is installed.
# ********************************************************************

from __future__ import with_statement

import os
import re

STR_TO_REPLACE = r"sys.exit"

REPLACEMENT_STR = (r"import subprocess\n"
                   r"    root_file_sys = subprocess.check_output(['df', '-h', '/'])\n"
                   r"    if root_file_sys and int(root_file_sys.split()[-2].split('%')[0]) >= 99:\n"
                   r"        print 'Exiting tool, root file system is currently greater than 98% full.'\n"
                   r"        exit(5)\n"
                   r"    sys.exit")


def update_entry_points():
    bin_dir = "/opt/ericsson/enmutils/bin"
    for file_path in [filename for filename in os.listdir(bin_dir)]:
        full_file_path = "{0}/{1}".format(bin_dir, file_path)
        # Catch IOErrors - sysmlinks, directories
        try:
            with open(full_file_path, "r") as f:
                file_data = f.read()
                file_string = (re.sub(STR_TO_REPLACE, REPLACEMENT_STR, file_data))
            if "root_file_sys" not in file_data:
                with open(full_file_path, "w") as file_handle:
                    file_handle.write(file_string)
        except EnvironmentError:
            pass


if __name__ == '__main__':  # pragma: no cover
    update_entry_points()
