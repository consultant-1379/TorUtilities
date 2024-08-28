#!/usr/bin/python
import os
import sys
import requests

try:
    import lxml.etree as et
except:
    import xml.etree.ElementTree as et

NEXUS_BASE_URL = "http://150.132.181.143:8081/nexus/service/local/repositories/releases/content/"


def _download_pom(group_id, artifact_id, latest_version, install_dir=None):
    artifact_url = "{0}{1}/{2}".format(NEXUS_BASE_URL, group_id.replace(".", "/"), artifact_id)
    pom_url = "{0}/{1}/{2}-{1}.pom".format(artifact_url, latest_version, artifact_id)
    result = False

    # Attempt to fetch the pom file
    response = requests.get(pom_url)

    if response.ok:
        # Figure out where to write the pom file
        if install_dir is not None:
            pom_path = os.path.join(install_dir, "pom.xml")
        else:
            pom_path = "pom.xml"

        print "Downloading {0}-{1}.pom from Nexus and saving to {2}...".format(artifact_id, latest_version, pom_path)

        # Write out the pom file
        with open(pom_path, 'wb') as file_handle:
            file_handle.write(response.content)

        result = True

    else:
        print "ERROR: Could not retrieve latest pom from Nexus"

    return result


def _prep_install_dir(install_dir):
    if install_dir is not None and not os.path.isdir(install_dir):
        os.makedirs(install_dir)


def _get_latest_version_of_artifact(group_id, artifact_id):
    # Build the full artifact URL
    artifact_url = "{0}{1}/{2}".format(NEXUS_BASE_URL, group_id.replace(".", "/"), artifact_id)

    # Make request to get list of all available versions of this artifact
    response = requests.get(artifact_url)

    # Return if we didn't get a status code of 200
    if response.status_code != 200:
        return None

    print "\nSuccessfully retrieved list of artifact versions from Nexus"

    # Parse the XML and figure out the latest version of the pom
    xml_root = et.fromstring(response.text)
    return xml_root.findall(".//text")[-1].text


def _print_help():
    """
    B{Prints help text}

    @rtype: void
    """
    print "\nDESCRIPTION"
    print "-----------"
    print "Automates the retrieval of the latest version of the specified artifact from Nexus"
    print "\nUSAGE"
    print "-----"
    print "get_pom_from_nexus.py <group-id> <artifact-id> [directory]"
    print "  where <group-id> is the group ID to target"
    print "  where <artifact-id> is the artifact ID to target"
    print "  where [directory] is the directory where the artifact is to be downloaded (optional)"
    print "\nEXAMPLE"
    print "-------"
    print "get_pom_from_nexus.py com.ericsson.nms.rv.taf torrv-testware taf-test"


def cli():
    install_dir = None

    # Check for help request
    if len(sys.argv) == 1 or sys.argv[1] in ["help", "-h"]:
        _print_help()
        return 0

    # Make sure that we were given 2-3 arguments
    if len(sys.argv) < 3:
        print "ERROR: Invalid number of command line arguments; 2 arguments required, and a 3rd argument is optional"
        _print_help()
        return 1

    # Gather command line arguments
    group_id = sys.argv[1].replace("/", "")
    artifact_id = sys.argv[2].replace("/", "")
    if len(sys.argv) == 4:
        install_dir = os.path.realpath(sys.argv[3])

    # Figure out the latest version of the testware available on Nexus
    latest_version = _get_latest_version_of_artifact(group_id, artifact_id)
    if latest_version is None:
        print "ERROR: Could not determine latest version of artifact on Nexus"
        return 1

    # Download the latest pom
    _prep_install_dir(install_dir)
    if not _download_pom(group_id, artifact_id, latest_version, install_dir):
        print "ERROR: Could not download latest pom file"
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(cli())
