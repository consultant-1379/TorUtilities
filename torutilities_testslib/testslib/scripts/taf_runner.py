#!/usr/bin/python
import os
import sys
import subprocess


def _run_cmd(cmd):
    print "\nExecuting '{0}'...\n".format(cmd)

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    while not process.poll():
        line = process.stdout.readline()
        if line:
            print line.strip()
        else:
            break

    return process.poll()


def _install_testware(test_dir):
    result = False

    # Check that the test directory contains a pom.xml file
    pom_path = os.path.join(test_dir, "pom.xml")

    if not os.path.exists(pom_path):
        print "ERROR: Did not find pom.xml file in test directory {0}".format(test_dir)
    else:
        print "Found pom.xml file at {0}".format(pom_path)

        rc = _run_cmd("cd {0}; mvn -X clean install -DskipTafTests".format(test_dir))
        if rc == 0:
            result = True

    return result


def _execute_testware(properties, test_dir):
    result = False

    rc = _run_cmd("cd {0}; mvn clean test {1}".format(test_dir, properties))
    if rc == 0:
        result = True

    return result


def _print_help():
    """
    B{Prints help text}

    @rtype: void
    """
    print "\nDESCRIPTION"
    print "-----------"
    print "Installs and executes TAF testware via Maven"
    print "\nUSAGE"
    print "-----"
    print "taf_runner.py <property string> [directory]"
    print "  where <property string> is a single string of one or more system properties to pass to Maven"
    print "  where [directory] is the directory containing the pom.xml file for the testware (optional)"
    print "\nEXAMPLE"
    print "-------"
    print "taf_runner.py '-Dtaf.cluster.id=174 -Dhost.gateway.ip=atvts972' taf-test"
    print "\nNOTE"
    print "-----"
    print "If the directory argument is not supplied, the tool expects to find a pom.xml file in the local"
    print "directory, which will be used to drive the testware installation and execution.  If a directory"
    print "argument is supplied, the tool will target the pom.xml file in that directory."


def cli():
    test_dir = None

    # Check for help request
    if len(sys.argv) == 1 or sys.argv[1] in ["help", "-h"]:
        _print_help()
        return 0

    # Make sure that we were given 1-2 arguments
    if len(sys.argv) < 2:
        print "ERROR: Invalid number of command line arguments; 1 argument required, and a 2nd argument is optional"
        _print_help()
        return 1

    # Get command line arguments
    properties = sys.argv[1]
    if len(sys.argv) == 3:
        test_dir = os.path.realpath(sys.argv[2])

    # Install the testware
    if not _install_testware(test_dir):
        print "ERROR: Could not install testware"
        return 1

    # Execute the testware
    if not _execute_testware(properties, test_dir):
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(cli())
