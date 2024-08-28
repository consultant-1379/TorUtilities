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
# ********************************************************************
# Name    : update_enmutils_rpm.py
# Purpose : Updates the ENM Utilities RPM package to either a user specified
#           version, or latest version.
# Team    : Blade Runners
# ********************************************************************

"""
update_enmutils_rpm - Updates ENM Utilites packages to either a user specified version,
                      or the latest available version (either by querying yum ms_repo at /var/www/html/ENM_ms - or Nexus
                      Packages this tool is concerned with:
                        - production (prod): ERICtorutilities_CXP9030570
                        - internal (int): ERICtorutilitiesinternal_CXP9030579
                      NOTE: This tool supports both upgrade and downgrade of the packages.

Usage:
  update_enmutils_rpm [VERSION] [--prod-only | --prod-and-int-only] [--auto-stop-invalid-profiles]
  update_enmutils_rpm -s | --status
  update_enmutils_rpm -l | --latest [--prod-only | --prod-and-int-only] [--auto-stop-invalid-profiles]

Arguments:
   VERSION        Is the version number of the upgrade

Examples:
    update_enmutils_rpm --latest --auto-stop-invalid-profiles
        Updates all packages (production, internal) to the latest version available in Nexus, and stops any invalid profiles in persistence

    update_enmutils_rpm -l --prod-and-int-only
        Updates all packages (production, internal) to the latest version available in Nexus

    update_enmutils_rpm
        Updates all packages (production, internal) to the version associated with the latest ERICtorutilities_CXP9030570 package, available in the yum ms_repo repository

    update_enmutils_rpm 4.13.1
        Updates all packages (production, internal) to version 4.13.1

    update_enmutils_rpm --prod-only
        Removes all dependent packages (internal) and only installs the latest version of ERICtorutilities_CXP9030570 package, available in the yum ms_repo repository

    update_enmutils_rpm --prod-and-int-only
        Removes any additional dependent packages, and only installs ERICtorutilities_CXP9030570 and ERICtorutilitiesinternal_CXP9030579 packages. Will use the version associated with the latest ERICtorutilities_CXP9030570 package available in the yum ms_repo repository

    update_enmutils_rpm 4.13.1 --prod-only
        Removes all dependent packages (internal) and only installs version 4.13.1 of the production ENM Utilities package

    update_enmutils_rpm 4.13.1 --prod-and-int-only
        Removes any additional dependent packages, and only installs version 4.13.1 of the ERICtorutilities_CXP9030570 and ERICtorutilitiesinternal_CXP9030579 packages

Options:
  -h        Print this help text
  -s --status  Overview of all available versions of the ENM Utilities package
  -l --latest  Latest version available on Nexus
  -a --auto-stop-invalid-profiles  Optional flag that when set will validate active profiles, stopping invalid profiles
"""

import glob
import os
import sys
from subprocess import call

import lxml.etree as etree
from docopt import docopt
from packaging import version as packaging_version


from enmutils_int.lib.profile_validation import stop_deleted_or_renamed_profiles
from enmutils_int.lib.nexus import METADATA, TEMP_DIR, TORUTILS_NEXUS_PATH, NEXUS_PROXY, check_deployment_to_disable_proxy
from enmutils.lib import shell, exception, http, init, log, thread_queue, filesystem
from enmutils.lib.exceptions import RpmMisMatch
from enmutils.lib import arguments as argumentsvar


MIN_SUPPORTED_VERSION = "4.13.1"
ALL_SUPPORTED_PACKAGES = ("prod", "int")
ENM_ISO_MATCH_REGEX = "ERICenm_CXP9027091-*iso"
ENM_ISO_LOCATION = "/var/tmp"
EXTRACT_RPM_VERSION_FROM_ISO_CMD = ("/usr/bin/isoinfo -lR -i {iso_path}  | grep {package} | cut -d'_' -f2 | cut -d'-' -f2 |  sed 's/\\.rpm//' | tr -d '\n'")
MS_REPO_NAME = "ms_repo"
GET_RPM_VERSION_WITH_REPOQUERY = '/usr/bin/repoquery -a --repoid={repo} --qf "{version}" {package}'
GET_VERSION_OF_INSTALLED_RPM_CMD = "rpm -q {package} | sed 's/-[^-]*$//' | sed 's/^.*-//g'"
PACKAGES = {"prod_package_name": "ERICtorutilities_CXP9030570",
            "int_package_name": "ERICtorutilitiesinternal_CXP9030579"}


def check_nexus_version(package_type, version_number=None):
    """
    Checks that the specified version exists on Nexus; returns the latest available version of the package otherwise

    :type package_type: str
    :param package_type: Package type to check, one of: prod, int
    :type version_number: str
    :param version_number: The version that the user wants to update to
    :return: latest version on nexus
    :rtype: str
    """

    version_to_install = None
    is_proxy_required = check_deployment_to_disable_proxy()

    # Get the contents of the xml page at the tor utilities nexus repo metadata

    try:
        response = http.get(METADATA.get("%s_torutils_repo_metadata" % package_type),
                            proxies=(NEXUS_PROXY if is_proxy_required else None), verbose=False)
    except http.requests.exceptions.ConnectionError:
        log.logger.error("Update cannot proceed as the artifactory is unavailable")
        response = None

    if response is not None and response.ok:
        response_xml_tree = etree.fromstring(response.content)

        # Make sure user's version number is in nexus repository
        if version_number is None:
            # Get the latest version number from the nexus http response
            version_to_install = response_xml_tree.find('versioning/release').text
        else:
            # Validate the version number provided by the user
            if not response_xml_tree.xpath("versioning/versions/version[text()='%s']" % version_number):
                log.logger.error("Could not find version number {0} for {1} package in Nexus artifactory".format(version_number, package_type))
            else:
                version_to_install = version_number

    return version_to_install


def _get_available_versions_from_nexus(package_list, version_number):
    """
    Builds a dictionary of packages and available versions of the package on Nexus

    :type package_list: list
    :param package_list: List of packages to update [prod, int]
    :type version_number: str
    :param version_number: The user-specified desired version or None
    :return: dictionary of available version on nexus
    :rtype: dict
    """

    available_versions_dict = {}

    for package in package_list:
        available_version = check_nexus_version(package, version_number)
        available_versions_dict[package] = available_version

    return available_versions_dict


def _is_installed(package):
    """
    Run rpm command to check if package is installed;

    :type package: str
    :param package: Name of package to search for. Ex. ERICtorutilities_CXP9030570;
    :return: resposne from local command
    :rtype: object
    """
    is_rpm_installed_cmd = "rpm -qa | grep {package}"
    cmd = is_rpm_installed_cmd.format(package=package)
    response = shell.run_local_cmd(shell.Command(cmd))
    return response


def _get_installed_version_of_package(package):
    """
    Returns the version of the package if it is installed; None if it is not installed

    :type package: str
    :param package: Name of package to search for
    :return: installed version of package
    :rtype: str or None
    """

    installed_version = None

    pkg_name = PACKAGES.get("{0}_package_name".format(package))
    if _is_installed(pkg_name).ok:
        cmd = GET_VERSION_OF_INSTALLED_RPM_CMD.format(package=pkg_name)
        response = shell.run_local_cmd(shell.Command(cmd))
        if response.ok:
            installed_version = response.stdout.strip()

    return installed_version


def _get_installed_versions(package_list):
    """
    Builds a dictionary of packages and the installed version of the package on the MS

    :type package_list: list
    :param package_list: List of packages to update [prod, int]
    :return: dictionary of installed version
    :rtype: dict
    """

    installed_versions_dict = {}

    for package in package_list:
        installed_versions_dict[package] = _get_installed_version_of_package(package)

    return installed_versions_dict


def _remove_unneeded_packages(package_list):
    """
    Uninstall all packages we are not up/downgrading

    :type package_list: list
    :param package_list: List of packages to update [prod, int]
    :raises RuntimeError: raises if install is unsuccessful
    """
    yum_erase_cmd = "/usr/bin/yum erase -y {rpms}"
    packages_to_erase = []
    for package_alias in package_list:
        if _get_installed_version_of_package(package_alias):
            packages_to_erase.append(PACKAGES.get("{0}_package_name".format(package_alias)))

    if packages_to_erase:
        packages_to_erase_str = ' '.join(packages_to_erase)
        cmd = yum_erase_cmd.format(rpms=packages_to_erase_str)
        response = shell.run_local_cmd(shell.Command(cmd))
        if response.ok:
            log.logger.info("Uninstalled: {0}".format(packages_to_erase_str))
        else:
            log.logger.error("Couldn't uninstall some packages from: {0}".format(packages_to_erase_str))
            raise RuntimeError("Unable to uninstall RPM {0}".format(packages_to_erase_str))


def _check_package_versions_match(available_versions_dict, package_list, version_number):
    """
    Check if the requested packages are valid and match

    :param available_versions_dict: Dictionary containing available versions
    :type available_versions_dict: dict
    :param package_list: List of packages to be installed
    :type package_list: list
    :param version_number: Version of the packages to be checked
    :type version_number: str

    :raises RuntimeError: raises if the package is inconsistent
    """
    # First check that all of the available versions are the same;
    # the same versions of all packages must be available in Nexus
    if len(set(available_versions_dict.values())) > 1:
        log.logger.error("Validation of the versions of available packages on Nexus has failed")
        for package in package_list:
            log.logger.error("  Version available on Nexus for package {0} is {1}".format(
                package, available_versions_dict[package]))
        raise RuntimeError("Inconsistent package versions available on Nexus; terminating update...")
    elif version_number is not None and available_versions_dict.values()[0] is None:
        raise RuntimeError("No packages have been found in Nexus with user specified version {0}".format(
            version_number))


def _get_package_update_list(package_list, version_number):
    """
    Builds a dictionary of packages and versions that are to be downloaded and installed

    :type package_list: list
    :param package_list: List of packages to update [prod, int]
    :type version_number: str
    :param version_number: The user-specified desired version or None
    :return: a list of package versions
    :rtype: tuple

    """
    # Check to see if the desired version is available in Nexus or
    # get the latest version if a specific version wasn't specified
    available_versions_dict = _get_available_versions_from_nexus(package_list, version_number)
    _check_package_versions_match(available_versions_dict, package_list, version_number)
    installed_versions_dict = _get_installed_versions(package_list)

    packages_to_update = []
    version = None

    # Next, check to see that the desired version of the package is not already installed;
    # if so, don't mark it to be downloaded and installed
    for package in package_list:
        if available_versions_dict[package] != installed_versions_dict[package]:
            packages_to_update.append(package)
            version = available_versions_dict[package]
            if available_versions_dict[package] is not None and installed_versions_dict[package] is not None:
                if packaging_version.parse(available_versions_dict[package]) >= packaging_version.parse(
                        installed_versions_dict[package]):
                    log.logger.info("Upgrading {0} RPM from version {1} to version {2}...".format(
                        package, log.blue_text(installed_versions_dict[package]),
                        log.purple_text(available_versions_dict[package])))
                else:
                    log.logger.info("Downgrading {0} RPM from version {1} to version {2}...".format(
                        package, log.blue_text(installed_versions_dict[package]),
                        log.purple_text(available_versions_dict[package])))
            elif installed_versions_dict[package] is None:
                log.logger.info("Installing {0} RPM version {1} (previously uninstalled)...".format(
                    package, log.purple_text(available_versions_dict[package])))

    _verify_packages_installed(packages_to_update, installed_versions_dict, available_versions_dict, package_list)

    return packages_to_update, version


def _verify_packages_installed(packages_to_update, installed_versions_dict, available_versions_dict, package_list):
    """
    Check if any packages can be updated or installed

    :param packages_to_update: List of packages to be verified
    :type packages_to_update: list
    :param installed_versions_dict: Dictionary containing the currently installed package versions
    :type installed_versions_dict: dict
    :param available_versions_dict: Dictionary containing available versions
    :type available_versions_dict: dict
    :param package_list: List of packages to be installed
    :type package_list: list

    :raises RuntimeError: raises if there are no packages to update
    """
    # Check if all of the packages are installed and are on latest versions
    if not packages_to_update:
        if installed_versions_dict == available_versions_dict:
            log.logger.warn('All packages are up to date with version {0}'.format(
                available_versions_dict[package_list[0]]))
        else:
            raise RuntimeError('Could not find any package to update. Check the logs.')


def _get_rpm_name(package, version):
    """
    Builds and returns the name of a versioned RPM

    :type package: str
    :param package: Name of the package to be downloaded
    :type version: str
    :param version: The version of the package to be downloaded
    :return: name of RPM version
    :rtype: str
    """

    return "{0}-{1}.rpm".format(PACKAGES.get("{0}_package_name".format(package)), version)


def _download_package(package, version):
    """
    Builds a dictionary of packages and versions that are to be downloaded and installed

    :type package: str
    :param package: Name of the package to be downloaded
    :type version: str
    :param version: The version of the package to be downloaded
    """

    rpm_file_name = _get_rpm_name(package, version)
    rpm_download_url = "{0}/{1}".format(TORUTILS_NEXUS_PATH, PACKAGES.get("{0}_package_name".format(package)))
    rpm_download_url = "{0}/{1}/{2}".format(rpm_download_url, version, rpm_file_name)

    local_rpm_file_path = os.path.join(TEMP_DIR, rpm_file_name)

    if filesystem.does_file_exist(local_rpm_file_path):
        filesystem.delete_file(local_rpm_file_path)

    log.logger.debug("Downloading {0} RPM from Nexus URL {1}...".format(package, rpm_download_url))
    is_proxy_required = check_deployment_to_disable_proxy()
    result = http.get(rpm_download_url, verify=False, proxies=(NEXUS_PROXY if is_proxy_required else None),
                      verbose=False)
    if result.ok:
        with open(local_rpm_file_path, 'wb') as file_handle:
            for chunk in result.iter_content():
                file_handle.write(chunk)


def _download_packages(packages, version):
    """
    Downloads the RPM packages that are to be installed or upgraded

    :type packages: list
    :param packages: List of packages to be downloaded
    :type version: str
    :param version: The version of the package to be downloaded
    :raises RuntimeError: raises if downloading failed from nexus
    """
    tq = thread_queue.ThreadQueue(work_items=packages, num_workers=len(packages), func_ref=_download_package, args=[version])
    tq.execute()

    # Make sure all files were downloaded succesfully
    for package in packages:
        rpm_file_name = _get_rpm_name(package, version)
        local_rpm_file_path = os.path.join(TEMP_DIR, rpm_file_name)

        if not filesystem.does_file_exist(local_rpm_file_path):
            raise RuntimeError("Unable to download RPM {0} from Nexus".format(rpm_file_name))
        else:
            log.logger.debug("RPM {0} successfully downloaded from Nexus".format(rpm_file_name))


def _install_packages(packages, version, snapped_version):
    """
    Attempts to install/upgrade the downloaded packages

    :type packages: list
    :param packages: List of packages to be downloaded
    :type version: str
    :param version: The version of the packages to be installed
    :param snapped_version: version of rpm before upgrade
    :type snapped_version: str
    :return: return code
    :rtype: int
    """
    log.logger.debug("Attempting to install TorUtils packages ({0} -> {1}".format(snapped_version, version))
    rc = 1

    # Build the list of packages
    package_paths_to_install = []

    for package in packages:
        rpm_file_name = _get_rpm_name(package, version)
        package_paths_to_install.append(os.path.join(TEMP_DIR, rpm_file_name))
    # Check if the rpm is being downgraded to an older enmscripting verison
    enm_user_2_update_required = _is_downgrade_of_rpm_below_particular_version(version, snapped_version, "4.65.12")
    # Files which need to be moved and copied
    env = "/opt/ericsson/enmutils/.env"
    site_packages_dir = "{0}/lib/python2.7/site-packages/".format(env)
    base_dir = "{0}/enmutils/".format(site_packages_dir)
    # User and library
    enm_user_2 = "{0}/lib/enm_user_2.py".format(base_dir)
    enmscripting_whl = "enm_client_scripting-1.16.1-py2.py3-none-any.whl"
    updated_library = "{0}/etc/{1}".format(base_dir, enmscripting_whl)
    # Temp locations
    enm_user_2_temp = "/var/tmp/enm_user_2.py"
    updated_library_temp = "/var/tmp/{0}".format(enmscripting_whl)
    if enm_user_2_update_required:
        log.logger.info("Copying existing enm_user_2.py to /var/tmp")
        filesystem.copy(enm_user_2, enm_user_2_temp)
        filesystem.copy(updated_library, updated_library_temp)

    # Build the command
    log.logger.debug("Packages to be installed: {0}".format(" ".join(package_paths_to_install)))
    cmd = "rpm -Uvh --replacepkgs --oldpackage {0}".format(" ".join(package_paths_to_install))
    response = shell.run_local_cmd(shell.Command(cmd, timeout=60 * 10, allow_retries=False))
    command = "rpm -qa | grep ERICtoru"
    response1 = shell.run_local_cmd(shell.Command(command))
    versions_installed = response1.stdout
    if len(versions_installed) > 100:
        command = "rpm -e $(rpm -qa |grep ERICtoru)"
        shell.run_local_cmd(shell.Command(command, log_cmd=False))
        cmd = "export LAST_GOOD_RPM={0}".format(snapped_version)
        shell.run_local_cmd(shell.Command(cmd))
        shell.run_local_cmd(shell.Command(
            "wget -O /root/torutils.rpm -e use_proxy=yes -e https_proxy=atproxy1.athtem.eei.ericsson.se:3128 " +
            "https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443/nexus/service/local/artifact/maven/redirect?r=\
                                         releases&g=com.ericsson.dms.torutility&a=ERICtorutilities_CXP9030570&v=$LAST_GOOD_RPM&e=rpm"))
        shell.run_local_cmd(shell.Command(
            "wget -O /root/torutils_int.rpm -e use_proxy=yes -e https_proxy=atproxy1.athtem.eei.ericsson.se:3128 " +
            "https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443/nexus/service/local/artifact/maven/redirect?r=\
                                          releases&g=com.ericsson.dms.torutility&a=ERICtorutilitiesinternal_CXP9030579&v=$LAST_GOOD_RPM&e=rpm"))
        shell.run_local_cmd(shell.Command("yum -y install /root/torutils.rpm /root/torutils_int.rpm"))

    if response.ok and "scriptlet failed" not in response.stdout and "syntax error" not in response.stdout:
        log.logger.info(log.green_text("\nAll RPMs installed successfully"))
        rc = 0
        if enm_user_2_update_required:
            _update_enmscripting_library(env, enmscripting_whl)
            log.logger.info("Copying newer enm_user_2.py from /var/tmp")
            filesystem.copy(enm_user_2_temp, enm_user_2)
    else:
        log.logger.error("\nOne or more RPMs failed to install")
        log.logger.error(response.stdout)

    # Remove all of the downloaded RPMs
    for path in package_paths_to_install:
        filesystem.delete_file(path)

    return rc


def update_enmutils_rpm(package_list=ALL_SUPPORTED_PACKAGES, version_number=None, auto_stop=False,
                        snapped_version=None):
    """
    Performs the RPM install and copies man pages to the man pages location

    :type package_list: list
    :param package_list: List of packages to update [prod, int]
    :type version_number: str
    :param version_number: The user-specified desired version or None
    :type auto_stop: bool
    :param auto_stop: Trigger to check if it should auto stop
    :param snapped_version: version of rpm before upgrade
    :type snapped_version: str
    :return: True if packages where installed else False
    :rtype: bool

    :raises RuntimeError: raises if no version_number specified and no litpd service installed
    """
    if not version_number and not os.path.exists("/usr/bin/litpd"):
        raise RuntimeError("Need to specify version if not running this tool on Vapp")

    _remove_unneeded_packages(list(set(ALL_SUPPORTED_PACKAGES) - set(package_list)))

    try:
        (packages_to_update, version_number) = _get_package_update_list(package_list, version_number)
    except BaseException as e:
        log.logger.error("\n{0}\n".format(e.args[0]))
        return 2

    if not packages_to_update:
        # Everything is up to date and nothing needs to be updated.
        return 0

    try:
        stop_deleted_or_renamed_profiles(version_number, auto_stop=auto_stop)
    except RpmMisMatch as e:
        log.logger.error("\n{0}\n".format(e.args[0]))
        return 2
    _download_packages(packages_to_update, version_number)
    return _install_packages(packages_to_update, version_number, snapped_version)


def get_status():
    """
    Gets all versions of ENM Utilities packages
    :return: all version of ENM Utilities packages
    :rtype: str
    """
    prod_pckg_alias = ALL_SUPPORTED_PACKAGES[0]
    pckg_ver_installed = _get_installed_version_of_package(prod_pckg_alias)
    pckg_version_local = get_package_version_from_yum_repo(MS_REPO_NAME, prod_pckg_alias)

    pkg_version_nexus = check_nexus_version(prod_pckg_alias)
    return """\nVersions of the ENM Utilities production package (ERICtorutilities_CXP9030570):
      - locally available: {0}
      - installed: {1}
      - latest available on Nexus: {2}\n""".format(pckg_version_local, pckg_ver_installed, pkg_version_nexus)


def get_latest_iso_version(pathname):
    """"
    Return the path to the latest version of enm iso. Paths are matching a pathname pattern.

    :type pathname: str
    :param pathname: Absolute path of an iso image. Regex can be used in pathname and may contain simple shell-style wildcards
    :return: path to latest version of iso
    :rtype: str
    """
    all_iso_versions = glob.glob(pathname)
    return max(all_iso_versions) if all_iso_versions else ''


def get_package_version_from_yum_repo(repo_name, package_alias):
    """
    Gets version of latest RPM package from provided yum repo

    :type repo_name: str
    :param repo_name: Name of a yum repo
    :type package_alias: str
    :param package_alias: Alias of a package, stored in the properties.conf - we need to find out version of. Example: prod
    :return: version of latest RPM
    :rtype: str
    """
    rpm_version = ''

    package = PACKAGES.get("{0}_package_name".format(package_alias))
    get_rpm_version_with_repoquery = GET_RPM_VERSION_WITH_REPOQUERY.format(repo=repo_name, version='%{version}', package=package)
    response = shell.run_local_cmd(shell.Command(get_rpm_version_with_repoquery))
    if response.ok and response.stdout.strip():
        rpm_version = response.stdout.strip()
    else:
        log.logger.error("\nCouldn't verify version of locally available package: {0} \n".format(package))
    return rpm_version


def get_package_version_from_iso(pathname, package_alias):
    """
    Gets a version of RPM package from an iso image located at provided pathname.

    :type pathname: str
    :param pathname: Absolute path of an iso image. Regex accepted
    :type package_alias: str
    :param package_alias: Alias of a package, stored in the properties.conf - we need to find out version of. Example: prod
    :return: version of RPM package
    :rtype: str
    """
    package = PACKAGES.get("{0}_package_name".format(package_alias))
    # In case of enm upgrade we would have at least 2 ENM isos,
    # we will choose the latest one in our query for package version
    chosen_iso = get_latest_iso_version(pathname)
    rpm_version = ''

    if chosen_iso:
        get_rpm_version_cmd = EXTRACT_RPM_VERSION_FROM_ISO_CMD.format(iso_path=chosen_iso, package=package)
        response = shell.run_local_cmd(shell.Command(get_rpm_version_cmd))
        if response.ok:
            rpm_version = response.stdout.strip()
        else:
            log.logger.error("\nCouldn't verify version of locally available package: {0}\n".format(package))
    else:
        log.logger.error("\nNo ENM iso was found at provided pathname: {0}\n".format(pathname))
    return rpm_version


def get_enm_iso_pathname_regex():
    """
    Returns regex to match pathname of the ENM iso

    :rtype: str
    :return: path to the enm iso
    """
    iso_regex = os.path.join(ENM_ISO_LOCATION, ENM_ISO_MATCH_REGEX)
    return iso_regex


def _is_upgrade(snapped_version, target_version):
    """
    Check if we have upgarde scenario
    :param snapped_version: version of rpm before upgrade
    :type snapped_version: str
    :param target_version: version of rpm after upgrade
    :type target_version: str
    :rtype: bool
    :return: True if upgrade scenario, False otherwise
    """
    return packaging_version.parse(target_version.strip()) > packaging_version.parse(snapped_version.strip())


def _is_downgrade_of_rpm_below_particular_version(target_version, current_version, particular_version):
    """
    Check if we are downgrading to a version of TorUtils below a particular version

    :param current_version: version of rpm before upgrade
    :type current_version: str
    :param target_version: version of rpm after upgrade
    :type target_version: str
    :param particular_version: version of rpm comparing against
    :type particular_version: str
    :rtype: bool
    :return: True if upgrade scenario, False otherwise
    """
    if not current_version:
        return False
    return (packaging_version.parse(current_version.strip()) >=
            packaging_version.parse(particular_version.strip()) >
            packaging_version.parse(target_version.strip()))


def _display_updated_profiles_after_rpm_upgrade(snapped_version, target_version):
    """Display updated profiles.
    There is no need to check for profiles to be restarted when we downgrade rpm - as
    UPDATE_VERSION stored on the profile instance will never be higher on the prev. rpm

    :param snapped_version: version of rpm before upgrade
    :type snapped_version: str
    :param target_version: version of rpm after upgrade
    :type target_version: str
    :rtype: bool
    :return: True when diff was called in the upgrade scenario, False otherwise
    """

    upgrade_scenario = _is_upgrade(snapped_version, target_version)
    if upgrade_scenario:
        call(['/opt/ericsson/enmutils/bin/workload', 'diff', '--updated'])
    return upgrade_scenario


def _update_enmscripting_library(env, whl_name):
    """
     Updates the installed verison of enmscripting when downgrading from a specific version

    :param env: Enmutils environment path
    :type env: str
    :param whl_name: Name of the .whl archive to be installed
    :type whl_name: str
    """

    if not filesystem.does_dir_exist('{0}/bin'.format(env)):
        log.logger.error("Unable to locate required virtualenv, downgrading is not recommended and may result in "
                         "reduced functionality.")
        return
    enmscripting_whl_path = "/var/tmp/{0}".format(whl_name)
    if not filesystem.does_file_exist(enmscripting_whl_path):
        log.logger.error("Unable to locate required {0} file, downgrading is not recommended and may result in "
                         "reduced functionality.".format(enmscripting_whl_path))
        return

    cmd = '{0}/bin/pip install {1}'.format(env, enmscripting_whl_path)
    log.logger.info("Pip installing newer version of enmscripting library. Command: {}".format(cmd))
    shell.run_local_cmd(shell.Command(cmd))


def cli():
    """B{Main flow}
    """
    tool_name = "update_enmutils_rpm"
    init.global_init("tool", "int", tool_name, sys.argv, execution_timeout=1800)

    # Process command line arguments
    try:
        arguments = docopt(__doc__)
    except SystemExit, e:
        # If there is a message that means we had invalid arguments
        if e.message:
            log.logger.info("\n {0}".format(e.message))
            exception.handle_invalid_argument()
        # Otherwise it is a call to help text
        else:
            raise

    # Check call for status
    if arguments['--status']:
        log.logger.info(get_status())
        rc = 0
        init.exit(rc)

    # Figure out which packages we should check
    packages = ALL_SUPPORTED_PACKAGES
    prod_package_alias = ALL_SUPPORTED_PACKAGES[0]

    if arguments["--prod-only"]:
        packages = ["prod"]
    elif arguments["--prod-and-int-only"]:
        packages = ["prod", "int"]

    # Check to see if we were given a specific version to install
    target_version = None
    snapped_version = _get_installed_version_of_package('int')

    if arguments["VERSION"]:
        target_version = arguments["VERSION"]
        argumentsvar.validate_version_number(target_version)

        # If a version number is supplied, make sure it's not older than MIN_SUPPORTED_VERSION
        if target_version and packaging_version.parse(target_version.strip()) < packaging_version.parse(MIN_SUPPORTED_VERSION):
            exception.handle_invalid_argument("ENM Utilities RPM packages aren't available for versions older than "
                                              "{0}".format(MIN_SUPPORTED_VERSION))

    rc = 2

    try:
        if arguments['--latest']:
            target_version = check_nexus_version(prod_package_alias)

        if not target_version:
            # Query MS for version of ERICtorutilities_CXP9030570 that came from the ENM iso
            # We expect it to be located in the ms_repo pointing to /var/www/html/ENM_ms/`
            # NOTE: don't want to query for the installed version
            # more: https://jira-oss.seli.wh.rnd.internal.ericsson.com/browse/TORF-79227
            target_version = (get_package_version_from_yum_repo(MS_REPO_NAME, prod_package_alias))

        rc = update_enmutils_rpm(packages, target_version, auto_stop=arguments['--auto-stop-invalid-profiles'],
                                 snapped_version=snapped_version)

    except:
        exception.handle_exception(tool_name)

    if rc < 2:
        log.logger.warn("\nIf running the tool from the enmutils/bin directory, please cd to ../bin as the update has "
                        "changed the filesystem\n")

    # Call "workload diff --updated" upon rpm upgrade
    if not rc and snapped_version and target_version:
        try:
            _display_updated_profiles_after_rpm_upgrade(snapped_version, target_version)
        except Exception as e:
            log.logger.warn("Failed to execute diff command, error encountered: {}".format(str(e)))

    init.exit(rc)


if __name__ == '__main__':
    cli()
