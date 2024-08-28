# ********************************************************************
# Name    : Profile Validation
# Summary : Used by the update_enmutils_rpm tool. Allows the tool to
#           query the existing load running and compare with the
#           Nexus profile information, identify any load not
#           supported by the RPM to be installed, and if selected
#           stop the mismatch in the load.
# ********************************************************************

from enmutils_int.lib.profile_manager import ProfileManager
from enmutils_int.lib.nexus import download_artifact_from_nexus
from enmutils_int.lib.py_json_html_converter import get_json_from_a_file, convert_from_json_to_dict
from enmutils_int.lib.load_mgr import get_active_profile_names, get_profile_objects_from_profile_names

from enmutils.lib import log
from enmutils.lib.exceptions import RpmMisMatch


def stop_deleted_or_renamed_profiles(rpm_version, auto_stop=False):
    """
    Method to handle the optional flow, when there are invalid profiles

    :param rpm_version: Version of rpm, which is being validated against
    :type rpm_version: str
    :param auto_stop: Boolean flag that indicates whether to stop the profiles or raise an exception to the user
    :type auto_stop: bool

    :raises RpmMisMatch: raised if there unknown profile executing not included in the rpm being installed.
    """
    missing = _artifact_versus_active_profiles(rpm_version)

    missing_profiles_list_excluding_specific_profiles = []
    for profile_name in missing:
        missing_profiles_list_excluding_specific_profiles.append(profile_name)

    if missing_profiles_list_excluding_specific_profiles:
        if auto_stop:
            _stop_missing_profiles(missing_profiles_list_excluding_specific_profiles)
            log.logger.info("The following profile(s): {0} have been either removed, renamed or were started "
                            "via a non-default schedule. "
                            "These profiles have now been stopped to allow upgrade to proceed."
                            .format(', '.join(missing_profiles_list_excluding_specific_profiles)))
        else:
            raise RpmMisMatch("\nThe following profile(s): {0} have been either removed, renamed or were started "
                              "via a non-default schedule."
                              "\nThese profiles need to be stopped to allow upgrade to proceed.\n"
                              .format(', '.join(missing_profiles_list_excluding_specific_profiles)))


def _artifact_versus_active_profiles(rpm_version):
    """
    Method to return a list of any active profiles, no longer included in the rpm

    :type rpm_version: str
    :param rpm_version: Version of rpm, which is being validated against

    :rtype: list
    :return: List of `profile.Profile` names
    """
    active_profiles = get_active_profile_names()
    rpm_dict = _fetch_dict_from_json(rpm_version)
    profs = set()
    for network in rpm_dict.itervalues():
        for app in network.itervalues():
            if app:
                for profile in app.iterkeys():
                    profs.add(profile)
    missing = active_profiles.difference(profs)
    return missing


def _fetch_dict_from_json(rpm_version):
    """
    Method to return a list of any active profiles, no longer included in the rpm

    :param rpm_version: Version of rpm, which is being validated against
    :type rpm_version: str

    :raises RpmMisMatch: raised if the rpm is not installable

    :return: Dictionary containing the profile_values.py generated with rpm in question
    :rtype: dict
    """
    group = 'com.ericsson.dms.torutility'
    artifact = 'ERICtorutilitiesinternal_CXP9030579'
    extension = 'json'

    local_file_path = download_artifact_from_nexus(group, artifact, rpm_version, extension)
    if not local_file_path:
        raise RpmMisMatch("Unable to download artifact for rpm: {}. Please ensure this is a valid rpm"
                          .format(rpm_version))
    artifact_dict = convert_from_json_to_dict(get_json_from_a_file(local_file_path)[0])
    return artifact_dict


def _stop_missing_profiles(missing):
    """
    Method to call stop function of the profiles identified as invalid

    :type missing: list
    :param missing: List of `profile.Profile` names

    :return: void
    """
    profiles = get_profile_objects_from_profile_names(missing)
    if profiles:
        log.logger.info("Invalid profiles detected - stopping them now...")
    for profile in profiles:
        ProfileManager(profile).stop()
