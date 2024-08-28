#!/usr/bin/python
import os
import subprocess
import pkgutil

BASE_DIR = os.path.join(pkgutil.get_loader('enmutils').filename, '..', '..')

PROPS_DIRS = ("{0}/ERICtorutilities_CXP9030570/enmutils/etc".format(BASE_DIR), "{0}/ERICtorutilitiesinternal_CXP9030579/enmutils_int/etc".format(BASE_DIR))


def _execute_command(cmd):
    """
    B{Run a local command and return the rc and stdout}

    @type cmd: string
    @param cmd: The local command to be run as a python subprocess
    @rtype: Tuple
    @return: Tuple where index 0 is return code and index 1 is stderr merged into stdout
    """

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    stdout = process.communicate()[0]
    return str(process.returncode), stdout


def _check_for_dupes_in_main_props_files():
    prod_props_file = os.path.join(PROPS_DIRS[0], "properties.conf")
    int_props_file = os.path.join(PROPS_DIRS[1], "properties.conf")

    prod_props = _get_props_from_file(prod_props_file)
    int_props = _get_props_from_file(int_props_file)

    dupe_counter = 0
    print "Checking for duplicated properties in production and internal properties.conf files..."
    for prop in sorted(prod_props.keys()):
        if prop in int_props:
            print "  {0}ERROR: Duplicate property {1}{2}{3} found in both prod and int properties.conf files{4}".format('\033[91m', '\033[94m', prop, '\033[91m', '\033[0m')
            dupe_counter = dupe_counter + 1

    if dupe_counter == 0:
        print "  No duplicates found"
    else:
        print ""


def _get_all_props_files():
    all_props_files = []

    for props_dir in PROPS_DIRS:
        (rc, stdout) = _execute_command("find {0} -name *.conf -print".format(props_dir))
        if rc == "0" and stdout is not None and len(stdout) > 0:
            props_files = stdout.split("\n")
            all_props_files.extend(props_files)

    return all_props_files


def _get_props_from_file(file_name):
    props = {}

    if file_name is not None and len(file_name) > 0:
        with open(file_name, "r") as file_handle:
            lines = file_handle.readlines()

        for line in lines:
            line = line.strip()
            if not line.startswith("#") and "=" in line:
                props[line.split("=")[0].strip()] = 1

    return props


def _get_all_props(props_files):
    all_props = {}

    print "Scanning for properties files..."
    for props_file in props_files:
        if props_file is not None and len(props_file) > 0:
            file_props = _get_props_from_file(props_file)
            all_props.update(file_props)

            print "  {0} [{1} props]".format(props_file, len(file_props))

    print "\n  Found {0} total properties across all properties files.\n".format(len(all_props))

    return all_props


def _search_for_references_to_props(all_props):
    search_cmd = r"""cd {0}; grep -rn -e "\"{1}\"" -e "'{1}'" ./* """
    full_search_cmd = "{0} | grep -E '(get_prop|/ui/flows/|/ui/tasks/)'".format(search_cmd)

    print "Checking for unused properties across the code base..."
    for prop in sorted(all_props.keys()):
        print "  {0}{1}{2}".format('\033[94m', prop, '\033[0m')

        cmd = full_search_cmd.format(BASE_DIR, prop)
        (rc, stdout) = _execute_command(cmd)

        if rc == "0" and stdout is not None and len(stdout) > 0:
            for line in stdout.split("\n"):
                if line is not None and len(line) > 0:
                    pass
                    # print "    {0}{1}{2}".format('\033[92m', line.strip(), '\033[0m')
        else:
            cmd = search_cmd.format(BASE_DIR, prop)
            (rc, stdout) = _execute_command(cmd)

            if rc == "0" and stdout is not None and len(stdout) > 0:
                print "    {0}WARN: No 'normal' references found for property {1}; searching for any instances of property...{2}".format('\033[33m', prop, '\033[0m')

                for line in stdout.split("\n"):
                    if line is not None and len(line) > 0:
                        print "  {0}{1}{2}".format('\033[33m', line.strip(), '\033[0m')
            else:
                print "    {0}ERROR: No references found for property {1}{2}".format('\033[91m', prop, '\033[0m')


def cli():
    # Get a dictionary of all properties we find across all properties files (prod and int)
    all_props = _get_all_props(_get_all_props_files())

    # Check for dupes
    _check_for_dupes_in_main_props_files()

    # Find references to properties in the code base and flag any properties that don't appear to have any references
    _search_for_references_to_props(all_props)


if __name__ == "__main__":
    cli()
