# ********************************************************************
# Name    : Profile Properties Manager
# Summary : Similar to profile manager, used at profile start up.
#           Primary functionality is to manage the injection of
#           attribute from custom configuration files at start up,
#           read and apply the respective framework configuration
#           values at start up.
# ********************************************************************

import re
import imp

from datetime import datetime

from enmutils.lib import log, config
from enmutils_int.lib import load_mgr as load_mgr
from enmutils_int.lib.common_utils import get_days_of_the_week
from enmutils_int.lib.workload_network_manager import InputData


class ProfilePropertiesManager(object):

    def __init__(self, profile_names, config_file=None):
        """
        Manages the extraction of properties from a config file and the profile_values.py.
        :param profile_names: list of profile names
        :type profile_names: list
        :param config_file: config file supplied by the user
        :type config_file: str
        """
        self.profile_names = profile_names
        self.config_file = self._load_config_file(config_file) if config_file else None

    @property
    def current_day(self):
        return datetime.now().strftime("%A").upper()

    def _inject_values_from_user_supplied_config_file(self, profile_obj):
        """
        Injects values from user supplied config file into the profile.
        :param profile_obj: profile object
        :type profile_obj: profile.Profile object
        """
        profile_name = getattr(profile_obj, "NAME")
        for k, v in getattr(self.config_file, profile_name).items():
            if not hasattr(profile_obj, k):
                log.logger.debug("Failed to find user defined attribute '%s' in profile %s, this MAY not be the "
                                 "correct attribute for this profile." % (k, profile_name))
            setattr(profile_obj, k, v)

    def _load_config_file(self, config_file):
        """
        Loads the config file

        :param config_file: str
        :type config_file: str
        :return: loaded config file
        :rtype: module
        :raises Exception: if failure to import the config file
        """
        profile_conf = ""
        try:
            profile_conf = imp.load_source('profile_conf', config_file)
        except Exception as e:
            log.logger.error("Failed to import profile config file: {0} ".format(str(e)))
            raise
        return profile_conf

    def get_profile_objects(self):
        """
        Sets the attributes on the provided profiles to those found in the config file, based on network metrics

        :return: list of  profile objects
        :rtype: list
        """

        profiles_not_in_config_file = []
        profile_names = []

        profile_objs = load_mgr.get_profile_objects_from_profile_names(self.profile_names)
        config_data = InputData()
        if config_data.pool:
            for profile_obj in profile_objs:
                profile_name = profile_obj.NAME
                app = re.split(r'_[0-9]', profile_name.lower())[0].replace('_setup', '')
                workload_item = config_data.get_profiles_values(app, profile_name)
                if workload_item is not None:
                    for k, v in workload_item.iteritems():
                        if config.has_prop('SOAK') and config.get_prop('SOAK'):
                            if k == 'SCHEDULED_DAYS':
                                v = get_days_of_the_week(upper=True)
                        setattr(profile_obj, k, v)

                if self.config_file:
                    if hasattr(self.config_file, profile_name):
                        self._inject_values_from_user_supplied_config_file(profile_obj)

                    else:
                        profiles_not_in_config_file.append(profile_obj)
                        profile_names.append(profile_name)

        log.logger.debug('These profiles are not present in the specified config file and will not be started: {0}'
                         .format(profile_names))
        profile_objs = [profile for profile in profile_objs if profile not in profiles_not_in_config_file]

        return profile_objs
