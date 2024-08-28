# ********************************************************************
# Name    : NEXUS
# Summary : Used by the update_enmutils_rpm tool. Responsible for
#           fetching the internal, production rpm information and
#           archives directly from nexus, also performs the upgrade,
#           downgrade of the production, internal rpms, triggers the
#           workload diff check and fetches the .json files from nexus.
# ********************************************************************


import os
import re
import time
from collections import OrderedDict

import lxml.etree as etree
import requests
from enmutils.lib import (http, log, cache)
from enmutils.lib.filesystem import does_file_exist, delete_file
from enmutils.lib.shell import Command, run_local_cmd
from enmutils_int.lib.configure_wlvm_operations import check_deployment_to_disable_proxy

requests.packages.urllib3.disable_warnings()

NEXUS_URL = 'https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443/nexus'
TORUTILS_NEXUS_PATH = '{0}/content/repositories/releases/com/ericsson/dms/torutility'.format(NEXUS_URL)
PRODUCTION_PKG_MAVEN_DATA_URL = "{0}/ERICtorutilities_CXP9030570/maven-metadata.xml".format(TORUTILS_NEXUS_PATH)
METADATA = {
    "prod_torutils_repo_metadata": PRODUCTION_PKG_MAVEN_DATA_URL,
    "int_torutils_repo_metadata": "{0}/ERICtorutilitiesinternal_CXP9030579/maven-metadata.xml".format(TORUTILS_NEXUS_PATH)}

# Needed to access nexus artifacts from the workload vm
NEXUS_PROXY = {'https': 'atproxy1.athtem.eei.ericsson.se:3128'} if not cache.is_host_ms() or "ENM_URL" in os.environ else None

DOWNLOAD_ARTIFACT_URL = "{nexus}/service/local/artifact/maven/redirect?r=releases&g={group}&a={artifact}&e={extension}&v={version}"
TEMP_DIR = "/tmp/enmutils"


def check_nexus_version(package_type, version_number=None):
    """
    Checks that the specified version exists on Nexus; returns None if invalid version; returns latest otherwise

    type package_type: str
    param package_type: Package type to check, one of: prod, int
    type version_number: str
    param version_number: The version that the use wants to validate. version_number=LATEST to get latest version in Nexus

    :return: Package version that exists on Nexus
    :rtype: str
    """

    verified_version = None
    response = None

    # Get the contents of the xml page at the tor utilities nexus repo metadata
    try:
        response = http.get(METADATA.get("%s_torutils_repo_metadata" % package_type), proxies=NEXUS_PROXY, verbose=False)
    except requests.exceptions.ConnectionError:
        log.logger.error("Update cannot proceed as the artifactory is unavailable")

    if response and response.ok:
        response_xml_tree = etree.fromstring(response.content)

        # Make sure user's version number is in nexus repository
        if not version_number or version_number.upper() == "LATEST":
            # Get the latest version number from the nexus http response
            verified_version = response_xml_tree.find('versioning/release').text
        else:
            # Validate the version number provided by the user
            if not response_xml_tree.xpath("versioning/versions/version[text()='%s']" % version_number):
                log.logger.error("Could not find version number {0} for {1} package in Nexus artifactory."
                                 .format(version_number, package_type))
            else:
                verified_version = version_number

    return verified_version


def download_artifact_from_nexus(group, artifact, version, extension, download_path=TEMP_DIR):
    """
    Download artifacts from Nexus
    :param group: group for the artifact
    :type group: str
    :param artifact: artifact to download
    :type artifact: str
    :param version: version for the artifact
    :type version: str
    :param extension: extension for the artifact
    :type extension: str
    :param download_path: path to directory where file should be downloaded to
    :type download_path: str
    :return: path to downloaded file or False
    :rtype: str
    """

    local_file_path = os.path.join(download_path, '{0}-{1}.{2}'.format(artifact, version, extension))
    if not os.path.isfile(local_file_path):
        _delete_old_artifacts(artifact)
        log.logger.debug(log.green_text("Downloading {0} artifact from Nexus to: {1}".format(artifact, local_file_path)))
        is_proxy_required = check_deployment_to_disable_proxy()
        response = http.get(DOWNLOAD_ARTIFACT_URL.format(nexus=NEXUS_URL, group=group, artifact=artifact,
                                                         extension=extension, version=version),
                            proxies=(NEXUS_PROXY if is_proxy_required else None), verify=False, verbose=False)
        if response.ok:
            with open(local_file_path, 'wb') as file_handle:
                for chunk in response.iter_content():
                    file_handle.write(chunk)

    if os.path.isfile(local_file_path):
        return local_file_path

    log.logger.error('ERROR: Could not save file: {0}'.format(local_file_path))
    return False


def download_mavendata_from_nexus(download_path=TEMP_DIR):
    """
    Download Maven Metadata xml file from Nexus

    :param: download_path: path to directory where file should be downloaded to
    :type: download_path: str
    :return: path to downloaded file or False
    :rtype: str or bool
    """
    filename = "maven-metadata.xml"
    local_file_path = os.path.join(download_path, filename)
    log.logger.debug("Downloading {0} from Nexus to: {1}".format(filename, local_file_path))

    if does_file_exist(local_file_path):
        delete_file(local_file_path)

    response = http.get(PRODUCTION_PKG_MAVEN_DATA_URL, proxies=NEXUS_PROXY, verify=False, verbose=False)
    if response.ok:
        with open(local_file_path, 'wb') as file_handle:
            for chunk in response.iter_content():
                file_handle.write(chunk)

    if does_file_exist(local_file_path):
        log.logger.debug("File downloaded to {0}".format(local_file_path))
        return local_file_path

    log.logger.error('ERROR: Could not save file to {0}'.format(local_file_path))
    return False


def _delete_old_artifacts(artifact):
    """
    Delete any artifacts that are over a week old
    :type artifact: str
    :param artifact: group for the artifact
    """
    older_than = 7 * 86400  # 1 week

    time_now = time.time()

    for tmp_file in os.listdir(TEMP_DIR):
        file_path = os.path.join(TEMP_DIR, tmp_file)
        if os.stat(file_path).st_mtime < time_now - older_than:
            if re.search(artifact, tmp_file):
                log.logger.debug("File removed as it is over a 7 days old: {0}".format(file_path))
                os.remove(file_path)


def get_released_rpm_version_per_sprint(sprint):
    """
    Returns version of torutilities rpm that has been released in the ENM isos
    ... and it would be nice to get this auto-populated

    :param sprint: Sprint,
    :type sprint: str

    :rtype: str or instance of OrderedDict
    :returns: version of rpm released in that specified sprint
    """
    rpms_released_on_enm_isos_per_sprint = {'16.12': '4.35.34', '16.13': '4.36.32', '16.14': '4.37.33',
                                            '16.15': '4.38.8', '16.16': '4.39.18', '17.1': '4.40.33', '17.3': '4.43.8',
                                            '17.5': '4.41.24', '17.6': '4.44.50', '17.7': '4.45.8', '17.9': '4.46.2',
                                            '22.5': '5.31.32', '22.6': '5.32.30'}

    # ordered = OrderedDict(sorted(rpms_released_on_enm_isos_per_sprint.items(), key=lambda t: t[0]))
    ordered = OrderedDict(sorted(rpms_released_on_enm_isos_per_sprint.items()))
    if sprint not in ['latest', 'all'] and sprint not in rpms_released_on_enm_isos_per_sprint.keys():
        sprint = 'previous'
    sprint = sprint.lower()
    if sprint == 'latest':
        last_item = list(ordered)[-1]
        return ordered[last_item]
    elif sprint == 'previous':
        last_item = list(ordered)[-2]
        return ordered[last_item]
    elif sprint == 'all':
        return ordered
    else:
        return ordered[sprint]


def _get_sprint():
    """
    Get previous sprint.

    :rtype: str
    :returns: version of prev sprint
    """
    sprint = 'previous'
    cmd = Command('cat /etc/enm-version')
    response = run_local_cmd(cmd)
    if response.ok and 'ENM' in response.stdout:
        sprint = re.findall(r'ENM [0-9]*.[0-9]*', response.stdout)[0].split(' ')[-1]
        if sprint:
            prefix = sprint.split('.')[0] if int(sprint.split('.')[-1]) > 1 else int(sprint.split('.')[-1]) - 1
            sprint = "{0}.{1}".format(prefix, int(sprint.split('.')[-1]) - 1)
    return sprint


def get_prev_sprint_relased_version():
    """
    Get rpm version released on ENM iso in the prev. sprint

    :rtype: str
    :returns: rpm version released on ENM iso in prev. sprint
    """
    # _TODO: automate
    # https://eteamspace.internal.ericsson.com/display/CIOSS/CIFWK+REST+Interfaces
    # https://ci-portal.seli.wh.rnd.internal.ericsson.com/getDropContents/?drop=16.16&product=ENM&mediaCategory=ms&pretty=true
    return get_released_rpm_version_per_sprint(_get_sprint())
