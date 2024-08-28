# ********************************************************************
# Name    : Workload Schedule
# Summary : Creates the workload schedule object. Responsible for
#           reading, parsing the full_schedule.py, manages the order
#           in which profiles will be started, and the sleep between
#           those profiles, triggers the stop and start operations,
#           performs management around unsupported and already
#           running profiles.
# ********************************************************************

import imp
import os
import time
from collections import OrderedDict

from enmutils.lib import exception
from enmutils.lib import log, filesystem, config, persistence, shell, mutexer
from enmutils.lib.exceptions import NoNodesAvailable
from enmutils_int.lib import profile_manager
from enmutils_int.lib.schedules import full_schedule


class WorkloadSchedule(object):

    def __init__(self, schedule_file=None, profile_dict=None, initial_install_teardown=False,
                 release_nodes=False, once_before_stability=False):
        """

        ScheduleFilter class used to filter out the profiles relevant for a ScheduleOperation object
        from a schedule file.

        :param schedule_file: a schedule_file path (eg. enmutils_int.lib.schedules import full_schedule.WORKLOAD).
        :type schedule_file: str
        :param profile_dict: dict of profiles to be used for a start or stop operation.
        :type profile_dict: dict
        :param initial_install_teardown: True if teardown methods do not need to be called.
        :type initial_install_teardown: bool
        :param release_nodes: True if the subsequent action, requires the release of exclusive nodes
        :type release_nodes: bool
        :param once_before_stability: Execute the action once as part of a stability run
        :type once_before_stability: bool
        """
        self.schedule = self.parse_schedule_file(schedule_file) if schedule_file else full_schedule.WORKLOAD
        self.profile_dict = profile_dict
        self.initial_install_teardown = initial_install_teardown
        self.once_before_stability = once_before_stability
        self.release_nodes = release_nodes

    @staticmethod
    def _finished(action):
        """ Log to the user that the operation has completed. """
        log.logger.info("Workload {0} initiation completed. Issue command 'workload"
                        " status' to see the status of the profiles. ".format(log.green_text(action)))

    def _sleep(self, sleep, profile):
        """
        Sleeps for a given sleep in seconds if not during an initial install teardown.

        :param sleep: time to put the profile to sleep
        :type sleep: int
        :param profile: name of the profile that is put to sleep
        :type profile: str
        """

        if not self.initial_install_teardown:
            log.logger.info("Profile {0} sleeping for {1} seconds.".format(log.green_text(profile), sleep))
            time.sleep(sleep)

    def get_profiles_from_schedule(self, profile_names):
        """
        Gets profiles from the schedule file along with sleep times for start and stop.

        :param profile_names: List of profile names to be added to the schedule
        :type profile_names: list

        :return: Ordered dict of profile values
        :rtype: dict
        """
        profiles = OrderedDict()
        for process in self.schedule:
            for application in process:
                for profile in process[application]:
                    if profile in profile_names:
                        profiles[profile] = process[application][profile]
        return profiles

    @staticmethod
    def parse_schedule_file(schedule_file):
        """
        Parses the schedule file if one is supplied by the user.

        :param schedule_file: path to schedule.
        :type schedule_file: str

        :return: The parsed schedule object
        :rtype: schedule or None
        """
        schedule_path = os.path.join(schedule_file)
        schedule = ""
        if filesystem.does_file_exist(schedule_path) and schedule_path.endswith(".py"):
            module_name = os.path.basename(schedule_path)[:-3]
            try:
                schedule = imp.load_source(module_name, schedule_path).WORKLOAD
            except Exception as e:
                log.logger.error("Schedule file malformed, Error :[{0}]; Example template file at "
                                 "/opt/ericsson/enmutils/etc/schedule_template.py".format(e))
                log.logger.info(log.blue_text("Starting/Stopping workload using the following schedule "
                                              "file: {0}.".format(schedule_path)))
            if schedule:
                log.logger.info("Using the following schedule file: {0}".format(schedule_path))
                return schedule
        else:
            log.logger.error(
                "Could not find schedule file {0}; please specify an existing schedule .py file.".format(schedule_path))
        return None

    def _execute(self, index, profile, profiles_in_schedule_order, sleeps, action="starting"):
        """
        Starts or Stops the profile depending on action and checks if there is multiple profiles to put them on sleep
        :param index: index of the profile
        :type index: int
        :param profile: Profile object that is executed
        :type profile: profile.Profile object
        :param profiles_in_schedule_order: list of profiles in order
        :type profiles_in_schedule_order: list
        :param sleeps: list of time to put profile to sleep depending on action
        :type sleeps:d list
        :param action: action that the profile is executing
        :type action: str
        :return: index
        :rtype: int
        """
        sleep = sleeps[0] if action == "starting" else sleeps[-1]
        index += 1
        try:
            profile = profile_manager.ProfileManager(self.profile_dict[profile], release_nodes=self.release_nodes)
            if action == "starting":
                try:
                    profile.start()
                except NoNodesAvailable:
                    sleep = 0
            else:
                profile.stop()
        except Exception as e:
            exception.process_exception(msg=e.message, print_msg_to_console=True)
        else:
            if not config.has_prop('SLEEP') or not config.get_prop('SLEEP'):
                self._sleep(sleep, profile.profile.NAME)
            else:
                if index < len(profiles_in_schedule_order):
                    self._sleep(sleep, profile.profile.NAME)
        return index

    def start(self):
        """
        Executes the start schedule operation
        """
        profiles_in_schedule_order = self.get_profiles_from_schedule([profile for profile in self.profile_dict.keys()])
        index = 0
        if profiles_in_schedule_order:
            for profile, sleeps in profiles_in_schedule_order.iteritems():
                if self.check_for_existing_process(profile):
                    continue
                index = self._execute(index, profile, profiles_in_schedule_order, sleeps)
        else:
            log.logger.error("No profiles found in the schedule. Add profile into 'full_schedule' module")
        self._finished("start")

    def stop(self):
        """ Executes the stop schedule operation """
        profiles_in_schedule_order = self.get_profiles_from_schedule([profile for profile in self.profile_dict.keys()])
        index = 0
        if profiles_in_schedule_order:
            for profile in reversed(profiles_in_schedule_order.keys()):
                sleeps = profiles_in_schedule_order[profile]
                index = self._execute(index, profile, profiles_in_schedule_order, sleeps, action="stopping")
        else:
            log.logger.error("No profiles found in the schedule.")

    @staticmethod
    def check_for_existing_process(profile):
        """
        Update the active profiles list at start up to prevent duplicates starting

        :param profile: Name of the profile to confirm is not already running
        :type profile: str

        :return: True if the profile is found to be running
        :rtype: bool
        """
        cmd = "ps -ef | grep '{0} {1}' | egrep -v grep".format(profile.upper(), profile.lower())
        response = shell.run_local_cmd(cmd)
        with mutexer.mutex("workload_profile_list", persisted=True):
            active_profiles = persistence.get("active_workload_profiles") or set()
            if profile.upper() in active_profiles or response.ok:
                log.logger.debug("Active Profiles: [{0}]".format(sorted(active_profiles)))
                log.logger.debug("Response: [{0}]".format(response.stdout))
                log.logger.error("Failed to start profile {0}, duplicate process found or currently included in active"
                                 " workload profiles list.\nCheck /var/log/enmutils/debug.log for more information"
                                 .format(profile))
                return True
