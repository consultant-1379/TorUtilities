# ********************************************************************
# Name    : Profile
# Summary : All workload profiles are a child of this module. Holds
#           all of the functionality required by profile in relation
#           to nodes, user management, scheduling, start up, exception
#           management, persisting and teardown.
# ********************************************************************

import cPickle as pickle
import os
import random
import re
import signal
import sys
import time
import datetime
from datetime import timedelta
from collections import defaultdict
from functools import partial
from logging import LoggerAdapter

from pexpect.exceptions import ExceptionPexpect
from requests.exceptions import HTTPError, ConnectionError, RequestException, BaseHTTPError
from websocket import (WebSocketTimeoutException, WebSocketBadStatusException, WebSocketConnectionClosedException,
                       WebSocketProtocolException)
from enmscripting.exceptions import TimeoutException
from enmutils.lib import process, persistence, mutexer, exception, log
from enmutils.lib.cache import is_emp
from enmutils.lib.enm_user_2 import SessionTimeoutException
from enmutils.lib.exceptions import (ScriptEngineResponseValidationError, ShellCommandReturnedNonZero, EnvironError,
                                     NoOuputFromScriptEngineResponseError, ENMJobStatusError, EnmApplicationError,
                                     MoBatchCommandReturnedError, NetsimError, ProfileError,
                                     EnvironWarning, NoNodesAvailable, ValidationWarning)
from enmutils.lib.log import get_profiles_logger
from enmutils_int.lib import node_pool_mgr, common_utils, status_profile
from enmutils_int.lib.enm_user import get_workload_admin_user
from enmutils_int.lib.services import usermanager_adaptor, nodemanager_adaptor
from enmutils_int.lib.services.profilemanager_adaptor import timestamp
from enmutils_int.lib.shm_utilities import SHMUtils

logger = None
_loop_generator = None
_iteration_number = 0

SLEEPING = 'SLEEPING'


def _get_logger():
    global logger
    if not logger:
        logger = get_profiles_logger()
    return logger


class Profile(object):
    PID_PATH = "/var/tmp/enmutils/daemon/{0}.pid"
    LOG_PATH = "/var/log/enmutils/daemon/{0}.log"
    IDENT_FILE_DIR = None  #
    THREADING_TEARDOWN_TIMER = 0  # Timer that holds the teardown method from executing
    EXCLUSIVE = False
    SETUP = False
    NODE_VERSION = None
    EXPORTABLE = True
    NODES_PER_HOST = None
    KEEP_RUNNING = True
    LOG_AFTER_COMPLETED = True
    PRIORITY = None
    RETAIN_NODES_AFTER_COMPLETED = False
    ERROR_LIMIT = 2000
    DEFAULT_MAX_RSS_MEMORY_MB = 5120  # i.e. 5GB

    def __init__(self):
        """
        Base Profile Constructor
        """

        self.teardown_list = TeardownList(self)
        self.pid = None
        self.start_time = timestamp.get_current_time()
        self._last_run = None
        self._next_run = None
        self.num_nodes = 0
        self.pidfile = os.path.abspath(os.path.realpath(self.PID_PATH.format(self.NAME)))
        self._state = None  # Valid states: "STARTING", "STOPPING", "RUNNING", "DEAD", "PARTIAL"
        self._initial_start = None
        self._sleep_time = None
        self.version = None
        self.update_version = None
        self.run_profile = True
        self.no_nodes_available = None
        self.is_completed = False
        self.next_run_time = None
        self.recent_scheduled_times_for_dst = []
        self.user_count = 0
        self.daily_error_count = 0
        self.reset_date = datetime.datetime.now().strftime("%d/%m/%Y")
        self.logged_exceeded_limit_message = False
        self.CLOUD_NATIVE_SUPPORTED = False

    @property
    def cloud(self):
        return is_emp()

    @property
    def _profile_error_key(self):
        return "%s-errors" % self.NAME

    @property
    def _profile_warning_key(self):
        return "%s-warnings" % self.NAME

    @property
    def priority(self):
        return self.PRIORITY or None

    @property
    def nodemanager_service_can_be_used(self):
        """
        Property to indicate if nodemanager service can be used

        :return: bool to indicate if service can be used or not
        :rtype: bool
        """
        return True if nodemanager_adaptor.can_service_be_used(profile=self) else False

    @property
    def ident_file_path(self):
        return self.PID_PATH.format(self.NAME)

    @property
    def supported(self):
        return hasattr(self, 'SUPPORTED') and self.SUPPORTED

    @property
    def logger(self):
        return LoggerAdapter(_get_logger(), {'profilename': self.NAME})

    @property
    def application(self):
        return self.NAME.split("_")[0]

    def __call__(self, teardown=False):
        """
        Initiates the setting up and tearing down of a profile depending on the teardown flag

        :type teardown: bool
        :param teardown: Flags whether the method should setup or teardown a profile
        :raises NotSupportedException: if profile not supported in cloud
        """
        self.pid = os.getpid()
        if teardown:
            self.state = "STOPPING"
            self.teardown(remove=True)
            return

        remove = False
        try:
            if hasattr(self, "SCHEDULED_TIMES_STRINGS"):
                self.SCHEDULED_TIMES = self.get_schedule_times()  # pylint: disable=W0201
            self.start_time = timestamp.get_current_time()
            self.version = common_utils.get_installed_version("ERICtorutilitiesinternal_CXP9030579")
            self.update_version = getattr(self, "UPDATE_VERSION", 0)
            self.state = "STARTING"
            self.logger.info('Profile state STARTING')
            if self.run_profile:
                self.run()
            self.pid = None  # Completed profile implies no running process, hence info needs to be persisted
            self.state = "COMPLETED"
            if self.num_nodes and not self.EXCLUSIVE and not self.RETAIN_NODES_AFTER_COMPLETED:
                node_mgr = nodemanager_adaptor if self.nodemanager_service_can_be_used else node_pool_mgr
                node_mgr.deallocate_nodes(self)
                self.num_nodes = 0
                self.is_completed = True
                self.persist()
            self.logger.info('Profile state COMPLETED')
            common_utils.terminate_user_sessions(getattr(self, 'NAME', "UNKNOWN"))
            self.kill_completed_pid()
            return
        except GeneratorExit as e:
            self.logger.info("Abnormal condition encountered - profile now exiting: {0}".format(str(e)))
            remove = True
        except KeyboardInterrupt:
            log.logger.debug("Profile (process id {0}) received SIGINT signal - profile will now be stopped"
                             .format(self.pid))
            self.state = "STOPPING"
            self.logger.info('Profile state STOPPING')
            remove = True
        except Exception as e:
            self.add_error_as_exception(e)
        self.teardown(remove=remove)

    def remove_partial_items_from_teardown_list(self):
        """
        Remove all partial items from teardown list
        """
        for item in self.teardown_list[:]:
            if isinstance(item, partial):
                self.teardown_list.remove(item)

    def kill_completed_pid(self):
        """
        Kills the daemon process if the profile is COMPLETED state
        Note: this will kill the currently running profile daemon process which is executing this code
        """
        log.logger.debug("Killing the process ID for {0} as the process is COMPLETED. This is to save memory. "
                         "There will be no further logging for: {0}".format(self.NAME))
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)
        try:
            process.kill_process_id(os.getpid(), signal.SIGTERM)  # self.pid = None, once profile is in COMPLETED state
        except OSError:
            return

    def run(self):
        raise NotImplementedError("No run method defined")

    @property
    def identifier(self):
        return '_'.join([self.NAME, self.get_timestamp_str()])

    @staticmethod
    def get_timestamp_str(timestamp_end_index=4):
        now = timestamp.get_current_time()
        return now.strftime("%m%d-%H%M%S%f")[0:-timestamp_end_index]

    @property
    def nodes(self):
        """
        Gets nodes from pool allocated to a profile

        :rtype: Dict of LoadNode objects
        :return: dict of allocated nodes
        """
        log.logger.debug("Get nodes from pool allocated to profile {0}".format(self.NAME))
        if self.nodemanager_service_can_be_used:
            used_nodes = defaultdict(list)
            for node in nodemanager_adaptor.get_list_of_nodes_from_service(profile=self.NAME, node_attributes=["all"]):
                used_nodes[node.primary_type].append(node)
            return used_nodes
        else:
            return node_pool_mgr.get_pool().allocated_nodes_as_dict(self)

    @property
    def running(self):
        """
        Checks if there is associated pid and if that pid is actually running on the system
        (If this is called by a running profile process, then no need to actually check that process is running)
        :rtype: bool
        :return: true if pid is running, else false
        """
        return self.pid and process.get_profile_daemon_pid(self.NAME) if self.pid != os.getpid() else True

    @property
    def daemon_died(self):
        """
        Determined whether a daemon that is expected to be running is dead

        :rtype: bool
        :return: True if daemon died
        """
        return self.state != "COMPLETED" and not self.running

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        """
        Persists load profile object after every state change.
        """
        log.logger.debug("Setting profile state to {0}".format(value))
        self._state = value
        self.persist()

    @property
    def status(self):
        if self.daemon_died:
            return "DEAD"
        elif self.warnings and not self.errors:
            return log.yellow_text("WARNING")
        elif self.errors:
            return "ERROR"
        return "OK"

    @property
    def errors(self):
        return persistence.get(self._profile_error_key)

    @property
    def warnings(self):
        return persistence.get(self._profile_warning_key)

    @property
    def schedule(self):
        """
        Gives the schedule information for the last and next iteration for a scheduled profile
        This information is printed in workload status

        :rtype: string
        :returns: String containing the last and next iteration information
        """
        timestats = self.set_time_stats_value()
        if hasattr(self, "SCHEDULED_TIMES"):
            if len(self.SCHEDULED_TIMES) > 10:
                times = [t.strftime('%H:%M') for t in sorted(self.SCHEDULED_TIMES) if
                         (t - datetime.datetime.now()).days >= 0]
                times_to_run = "{0} [next 10 run times] ".format(', '.join(times[:10]))
            else:
                times_to_run = ', '.join(t.strftime('%H:%M') for t in sorted(self.SCHEDULED_TIMES))
            if hasattr(self, "SCHEDULED_DAYS"):
                message = 'Runs at the following times: {0} on {1} {2}'.format(times_to_run,
                                                                               ",".join(self.SCHEDULED_DAYS), timestats)
            else:
                message = 'Runs at the following times: {0} {1}'.format(times_to_run, timestats)
            return message
        elif hasattr(self, 'SCHEDULE_SLEEP'):
            if self.SCHEDULE_SLEEP <= 0.5:
                return "CONSTANT"
            sleep_schedule = str(datetime.timedelta(seconds=self.SCHEDULE_SLEEP))

            return 'Every %s %s' % (sleep_schedule, timestats)
        else:
            return 'No scheduling is applied to this profile'

    def set_time_stats_value(self):
        """
        Set the last run and next runs for the schedule property

        :return: String containing the last run and next run values at this point
        :rtype: str
        """
        time_fmt = "%d-%b %H:%M:%S"
        now = "[NOW]"
        last_run = self._last_run.strftime(time_fmt) if self._last_run else "[NEVER]"
        if self.state:
            next_run = self._next_run.strftime(
                time_fmt) if self._next_run and not self._initial_start else self._initial_start or now
            next_run = self.next_run_time.strftime(
                time_fmt) if self.next_run_time and next_run == now else next_run
        else:
            next_run = "[When Profile Starts]"

        time_stats = "(last run: {0}, next run: {1})".format(last_run, next_run)
        return time_stats

    def sleep(self):
        """
        Sleeps for the period specified in the profile class and sets schedule information
        """
        # Next_run is now equal to last run. Last run + schedule time = time we should wake at
        # If now < time we should wake at we sleep the difference

        global _iteration_number
        if isinstance(self.KEEP_RUNNING, int) and _iteration_number >= self.KEEP_RUNNING:
            log.logger.debug("Returning without sleeping as this is the last iteration.")
            return

        sleep = True
        if self._next_run and (self._next_run + datetime.timedelta(seconds=self.SCHEDULE_SLEEP) <
                               datetime.datetime.now() - datetime.timedelta(seconds=2)):
            sleep = False

        # Last run will only be "now" for the first iteration because the next run is never None after this iteration
        self._last_run = self._next_run if self._next_run else datetime.datetime.now()

        # If we are not sleeping then the next_run is going to be now
        self._next_run = (self._last_run + datetime.timedelta(seconds=self.SCHEDULE_SLEEP)
                          if sleep else datetime.datetime.now())
        time_now = datetime.datetime.now()
        sleep = False if time_now > self._next_run else True

        if sleep:
            sleep_datetime = self._next_run - time_now
            log.logger.debug("Time Now: {0}".format(str(time_now)))
            log.logger.debug("Time Next Run: {0}".format(str(self._next_run)))

            old_state = self.state
            self.state = "SLEEPING"
            log.logger.debug("Sleeping for {0} seconds until next iteration".format(sleep_datetime.total_seconds()))
            if int(sleep_datetime.total_seconds()) > 3600 and self.user_count:
                common_utils.terminate_user_sessions(getattr(self, 'NAME', 'UNKNOWN'))
            self.logger.info('Profile state SLEEPING for {0} seconds. Next iteration at {1}'
                             .format(sleep_datetime.total_seconds(), str(self._next_run)))
            self._log_when_sleeping_for_gt_four_hours(sleep_datetime.total_seconds())
            self.state = old_state
            self.logger.info('Profile is running its next iteration now')
        else:
            self.persist()
            log.logger.debug("Running next iteration immediately as time to run profile was greater than the sleep "
                             "time")
            self.logger.info('Profile is running its next iteration immediately')

    @staticmethod
    def calculate_dst_offset_for_next_iteration(current_timestamp_secs, next_iteration_sleep_time_secs):
        """
        Calculate the offset to be applied in the next iteration based on whether DST is active or not for current time

        :param current_timestamp_secs: Number of seconds since Epoch (Jan 1st 1970)
        :type current_timestamp_secs: float
        :param next_iteration_sleep_time_secs: Number of seconds since Epoch (Jan 1st 1970) to next iteration
        :type next_iteration_sleep_time_secs: float
        :return: Number of seconds to the next scheduled iteration
        :rtype: int
        """
        start_time_dst_offset = 0

        if time.daylight:
            offset_local_dst_timezone_secs = time.altzone
            offset_local_non_dst_timezone_secs = time.timezone
            dst_offset_secs = offset_local_dst_timezone_secs - offset_local_non_dst_timezone_secs

            dst_enabled_for_current_timestamp = time.localtime(current_timestamp_secs).tm_isdst
            dst_enabled_for_next_iteration_timestamp = time.localtime(
                current_timestamp_secs + next_iteration_sleep_time_secs).tm_isdst
            if dst_enabled_for_current_timestamp and not dst_enabled_for_next_iteration_timestamp:
                start_time_dst_offset -= dst_offset_secs

            if not dst_enabled_for_current_timestamp and dst_enabled_for_next_iteration_timestamp:
                start_time_dst_offset += dst_offset_secs

        return start_time_dst_offset

    def sleep_until_day(self, delay_secs=0):
        """
        Sleeps until specific day (irrespective of what day is set in the scheduled times)
        Once this function is used once it must be used in all subsequent iterations
        (i.e sleep_until should not longer be used)

        :type delay_secs: int
        :param delay_secs: Number of seconds to reduce sleep time to perform dynamic node allocation process
        """
        DAYS = ["SATURDAY", "SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]

        time_now = datetime.datetime.now()
        current_day_index = DAYS.index(time_now.strftime('%A').upper())
        updated_days = DAYS[current_day_index:] + DAYS[0:current_day_index]

        # Reset all the schedule times so they'll only be examining specific days
        dto = [updated_days.index(day) for day in self.SCHEDULED_DAYS if day in updated_days]

        for index in range(len(self.SCHEDULED_TIMES)):
            updated_schedule = time_now + timedelta(days=min(dto))
            new_schedule = self.SCHEDULED_TIMES[index].replace(year=updated_schedule.year,
                                                               month=updated_schedule.month, day=updated_schedule.day)
            # Check if updated scheduled time is in the past
            if (new_schedule - datetime.datetime.now()).total_seconds() < 0:
                if len(dto) == 1:
                    updated_schedule = time_now + timedelta(days=7)
                else:

                    dto.sort()
                    updated_schedule = time_now + timedelta(days=dto[1])
                new_schedule = new_schedule.replace(year=updated_schedule.year, month=updated_schedule.month,
                                                    day=updated_schedule.day)

            # Set the new schedule
            self.SCHEDULED_TIMES[index] = new_schedule
        self._sleep_until(delay_secs)

    def sleep_until_time(self, delay_secs=0):
        """
        Sleeps until specific time (irrespective of what day is set in the scheduled times)
        Once this function is used once it must be used in all subsequent iterations
        (i.e sleep_until should not longer be used)

        :type delay_secs: int
        :param delay_secs: Number of seconds to reduce sleep time to perform dynamic node allocation process
        """
        time_now = datetime.datetime.now()
        # Reset all the schedule times so they'll only be examining today times
        for index in range(len(self.SCHEDULED_TIMES)):
            if hasattr(self, 'SCHEDULE_SLEEP_DAYS') and self.SCHEDULE_SLEEP_DAYS:  # when profile runs for once
                # every specific days with particular time Ex: Runs once every 2 days at 22.30 (10.30 PM)
                self.SCHEDULED_TIMES[index] = (self.SCHEDULED_TIMES[index].replace(
                    year=time_now.year, month=time_now.month, day=time_now.day) + timedelta(days=self.SCHEDULE_SLEEP_DAYS))
            else:
                self.SCHEDULED_TIMES[index] = self.SCHEDULED_TIMES[index] \
                    .replace(year=time_now.year, month=time_now.month, day=time_now.day)

        self._sleep_until(delay_secs)

    def _sleep_until(self, delay_secs=0):
        """
        Determines the next scheduled running time, and sleeps until time has been reached

        :type delay_secs: int
        :param delay_secs: Number of seconds to reduce sleep time to perform dynamic node allocation process
        """
        current_time_in_secs_since_epoch = int(time.time())
        current_local_time = datetime.datetime.fromtimestamp(current_time_in_secs_since_epoch)
        log.logger.debug("Number of seconds since epoch: {0}, current local time: {1}"
                         .format(current_time_in_secs_since_epoch, current_local_time))

        self._last_run = self._next_run if self._next_run else current_local_time

        if self.SCHEDULED_TIMES and current_local_time not in self.SCHEDULED_TIMES:
            self.calculate_time_to_wait_until_next_iteration(current_time_in_secs_since_epoch, delay_secs)

            old_state = self.state
            self.state = SLEEPING

            self.logger.info('Profile state SLEEPING for {0} seconds. Next iteration at {1}'
                             .format(self._sleep_time, self.next_run_time))
            log.logger.debug("Sleeping for {0} seconds until next scheduled run at {1}."
                             .format(self._sleep_time, self.next_run_time))
            self._log_when_sleeping_for_gt_four_hours(self._sleep_time)

            self.state = old_state
            self.logger.info('Profile is running its next iteration now')
        else:
            log.logger.debug("Unexpected behaviour - SCHEDULED_TIMES not set")
            time.sleep(1)
            self.logger.info('Profile is running its next iteration now')

    def calculate_time_to_wait_until_next_iteration(self, current_time_in_secs_since_epoch, delay_secs=0):
        """
        Calculates the time to wait until next iteration

        :param current_time_in_secs_since_epoch: Current time in secs since epoch
        :type current_time_in_secs_since_epoch: int
        :type delay_secs: int
        :param delay_secs: Number of seconds to reduce sleep time to perform dynamic node allocation process
        """
        wait_times = {}

        for scheduled_timestamp in self.SCHEDULED_TIMES:
            secs_until_scheduled_time, dst_offset, updated_scheduled_timestamp = (
                self.calculate_dst_adjusted_diff_between_timestamps(current_time_in_secs_since_epoch,
                                                                    scheduled_timestamp))
            if secs_until_scheduled_time < 0:
                continue

            if updated_scheduled_timestamp in self.recent_scheduled_times_for_dst:
                log.logger.debug("The profile has already executed at scheduled time ({0}), "
                                 "e.g. around time of DST deactivation".format(updated_scheduled_timestamp))
                continue

            wait_times[secs_until_scheduled_time] = {}
            wait_times[secs_until_scheduled_time]["scheduled_timestamp"] = updated_scheduled_timestamp
            wait_times[secs_until_scheduled_time]["dst_offset"] = dst_offset

        if wait_times:
            minimum_waiting_time = min([s for s in wait_times.iterkeys()])
            actual_time_to_run_at = wait_times[minimum_waiting_time]["scheduled_timestamp"]
            log.logger.debug("Next iteration detected: {0}, DST Offset: {1}"
                             .format(actual_time_to_run_at, wait_times[minimum_waiting_time]["dst_offset"]))

            self._sleep_time = minimum_waiting_time
            # Modify sleep time with provided snooze value
            if delay_secs and self._sleep_time > delay_secs:
                self._sleep_time = self._sleep_time - delay_secs
                log.logger.debug("Sleep time value was reduced to {0} secs and new sleep time value before dst check "
                                 "is {1}".format(delay_secs, self._sleep_time))
            self.next_run_time = actual_time_to_run_at
            self.update_recent_scheduled_times_for_dst()

    def update_recent_scheduled_times_for_dst(self):
        """
        Update the list of recent scheduled times if DST timezone defined
        """
        if time.daylight:  # if DST timezone is defined

            offset_local_dst_timezone_secs = time.altzone
            offset_local_non_dst_timezone_secs = time.timezone
            dst_offset_secs = offset_local_dst_timezone_secs - offset_local_non_dst_timezone_secs
            for scheduled_time in self.recent_scheduled_times_for_dst[:]:
                if (self.next_run_time - scheduled_time).total_seconds() > 2 * abs(dst_offset_secs):
                    self.recent_scheduled_times_for_dst.remove(scheduled_time)

            self.recent_scheduled_times_for_dst.append(self.next_run_time)

    def calculate_dst_adjusted_diff_between_timestamps(self, current_time_in_secs_since_epoch, scheduled_timestamp):
        """
        Calculate the time difference between 2 timestamps adjusted for DST

        :param current_time_in_secs_since_epoch: Current time in secs since epoch
        :type current_time_in_secs_since_epoch: int
        :param scheduled_timestamp: Timestamp to which is being measured from reference timestamp
        :type scheduled_timestamp: datetime.datetime

        :return: Difference in seconds, adjusted for DST, between 2 timestamps
        :rtype: int
        """
        current_timestamp = datetime.datetime.fromtimestamp(current_time_in_secs_since_epoch)

        secs_until_scheduled_time = int((scheduled_timestamp - current_timestamp).total_seconds())

        if secs_until_scheduled_time < 0:  # scheduled_timestamp is earlier then current_timestamp on same day
            scheduled_timestamp += timedelta(days=1)
            secs_until_scheduled_time = int((scheduled_timestamp - current_timestamp).total_seconds())

        dst_offset = self.calculate_dst_offset_for_next_iteration(current_time_in_secs_since_epoch,
                                                                  secs_until_scheduled_time)
        if dst_offset < 0:
            secs_until_scheduled_time += dst_offset
        else:
            secs_until_scheduled_time -= -dst_offset

        return secs_until_scheduled_time, dst_offset, scheduled_timestamp

    def persist(self):
        """
        Updates object in persistence

        :raises GeneratorExit: if ConnectionError occurs when trying to store object in persistence

        """
        if not persistence.has_key(self.NAME):
            with mutexer.mutex("workload_profile_list", persisted=True):
                active_profiles = persistence.get("active_workload_profiles") or set()
                active_profiles.add(self.NAME)
                persistence.set("active_workload_profiles", active_profiles, -1)
        try:
            log.logger.debug("Size of profile object after pickling is {0}".format(
                sys.getsizeof(pickle.dumps(self, pickle.HIGHEST_PROTOCOL))))
            persistence.set(self.NAME, self, -1)
            self.set_status_object()
            self.set_diff_object()
            self.check_profile_memory_usage()
        except ConnectionError as e:
            log.logger.debug("================= Found a ConnectionError ====================")
            log.logger.debug("Profile_Name: {0}\n Profile_Object_value: {1}\n Error: {2}".format(self.NAME, self, e))
            raise GeneratorExit("Profile object could not be stored in persistence")
        except Exception:
            exception.process_exception()

    def set_status_object(self):
        """
        Set the status object in Redis
        """
        user_count = getattr(self, "user_count", 0)
        status_values = {"name": self.NAME, "state": self.state, "start_time": self.start_time, "pid": self.pid,
                         "num_nodes": self.num_nodes, "schedule": self.schedule, "priority": self.priority,
                         "last_run": self.get_last_run_time(), "user_count": user_count}
        prof = status_profile.StatusProfile(**status_values)
        persistence.set('{0}-status'.format(self.NAME), prof, -1)

    def set_diff_object(self):
        """
        Set the diff object in Redis
        """
        diff_values = {"name": self.NAME, "state": self.state, "start_time": self.start_time, "version": self.version,
                       "update_version": self.update_version, "supported": self.supported}
        diff_profile = DiffProfile(**diff_values)
        persistence.set('{0}-diff'.format(self.NAME), diff_profile, -1)

    def check_profile_memory_usage(self):
        """
        Check Memory usage of process

        :raises GeneratorExit: if RSS memory usage exceeds Max Memory limit
        """
        log.logger.debug("Checking RSS memory usage by profile")
        rss_memory_used_by_profile_daemons = 0
        running_pids = process.get_profile_daemon_pid(self.NAME)
        for pid in running_pids:
            rss_memory_used_by_profile_daemons += process.get_current_rss_memory_for_current_process(pid=int(pid))

        rss_memory_used_by_profile_daemons_mb = rss_memory_used_by_profile_daemons / 1024
        max_rss_memory_allowed_mb = getattr(self, "MAX_RSS_MEMORY_MB", self.DEFAULT_MAX_RSS_MEMORY_MB)

        if rss_memory_used_by_profile_daemons_mb > max_rss_memory_allowed_mb:
            log.logger.debug("Total RSS Memory used ({0} MB) by daemon processes belonging to profile has exceeded "
                             "maximum RSS memory usage allowed per profile ({1} MB)."
                             .format(rss_memory_used_by_profile_daemons_mb, max_rss_memory_allowed_mb))

            if getattr(self, "AUTOSTOP_ON_MAX_RSS_MEM_REACHED", True):
                log.logger.debug("As this is deemed to be excessive memory usage, the profile will be shutdown now in "
                                 "order to protect the stability of the server. "
                                 "This problem should be followed up with profile design team.")

                log.logger.debug("To override this protection mechanism, the following variables can be set for this "
                                 "profile in the profile values file before the profile is started: "
                                 "1) MAX_RSS_MEMORY_MB limit set to larger value than {0} MB, or "
                                 "2) AUTOSTOP_ON_MAX_RSS_MEM_REACHED set to False"
                                 .format(max_rss_memory_allowed_mb))

                raise GeneratorExit("Profile daemon RSS memory usage exceeded maximum allowed limit ({0} MB)"
                                    .format(max_rss_memory_allowed_mb))
            else:
                log.logger.debug("Automatic stop of profile (AUTOSTOP_ON_MAX_RSS_MEM_REACHED) is not enabled - "
                                 "profile will continue to run despite combined RSS memory usage (by profile daemons) "
                                 "exceeding limit set on profile")

    @staticmethod
    def _process_error_for_type(e):
        if isinstance(e, NetsimError):
            error_type = NetsimError().__class__.__name__
        elif isinstance(e, (EnvironError, WebSocketTimeoutException, ExceptionPexpect, BaseHTTPError)):
            error_type = EnvironError().__class__.__name__
        elif isinstance(e, (EnmApplicationError, RequestException, TimeoutException,
                            WebSocketBadStatusException, WebSocketConnectionClosedException,
                            WebSocketProtocolException, SessionTimeoutException)):
            error_type = EnmApplicationError().__class__.__name__
        elif isinstance(e, EnvironWarning):
            error_type = EnvironWarning().__class__.__name__
        elif isinstance(e, ValidationWarning):
            error_type = ValidationWarning().__class__.__name__
        else:
            error_type = ProfileError().__class__.__name__
        return error_type

    @staticmethod
    def _extract_html_text(html_body):
        """
        Extract text from html

        :type html_body: str
        :param html_body: Html file to extract info from
        :rtype: str
        :return: result of extracted text
        """
        return extract_html_text(html_body)

    @staticmethod
    def update_error_message_for_connection_error(error, exception_msg):
        """
        Call the appropriate function to generate an error message depending on error type

        :param error: Error to generate message for.
        :type error: HTTPError or ConnectionError
        :param exception_msg: Current error message
        :type exception_msg: str
        :return: Error message
        :rtype: str
        """

        if isinstance(error, HTTPError):
            return set_http_error(error, exception_msg)
        else:
            return set_connection_error(error, exception_msg)

    @staticmethod
    def update_error_message_with_custom_length(error):
        """
        Generate error message with custom length depending on error type
        :param error: Exception to be build error message for
        :type error: BaseException
        :return: tuple containing error length and error message
        :rtype: tuple
        """

        error_length = 200
        error_message = str(error)

        if isinstance(error, NoOuputFromScriptEngineResponseError):
            error_length = 700
            error_message = (
                "NoOuputFromScriptEngineResponseError: ScriptEngineCommand '{command}' "
                "failed with status code {status_code}."
                .format(command=error.response.command[:error_length], status_code=error.response.http_response_code()))
        elif isinstance(error, ShellCommandReturnedNonZero):
            error_length = 2000
            error_message = ("ShellError: Command '{command}' gave rc '{rc}'\nResponse: '{stdout}'"
                             .format(command=error.response.command, rc=error.response.rc,
                                     stdout=error.response.stdout[:error_length]))

        return error_length, error_message

    def add_error_as_exception(self, e, log_trace=True):
        """
        Constructs an error_message for workload status from a given exception.
        Max errors/day: 2000

        :type e: Exception
        :param e: Exception from which to extract error_message
        :type log_trace: bool
        :param log_trace: Flags whether to log the stack trace
        """

        if self.check_if_error_limit_reached():
            return

        error_length = 200
        if log_trace:
            exception.process_exception()
        error_type = self._process_error_for_type(e)
        error_message, warning_message = None, None
        exception_msg = str(e)

        if isinstance(e, (HTTPError, ConnectionError)):
            error_message = self.update_error_message_for_connection_error(e, exception_msg)
        elif isinstance(e, (NoOuputFromScriptEngineResponseError, ShellCommandReturnedNonZero)):
            error_length, error_message = self.update_error_message_with_custom_length(e)
        elif isinstance(e, ENMJobStatusError):
            error_message = ("ENMJobStatusError: Job {command} raised ENMJobStatusError {exception}."
                             .format(command=e.response.command, exception=e.message))
        elif isinstance(e, ScriptEngineResponseValidationError):
            error_message = set_script_engine_error(e)
        elif isinstance(e, MoBatchCommandReturnedError):
            try:
                error_message = "Failure: Check AMOS service or Node" + str((re.findall(r'(.*\(no contact\))|(.*\(amos error\))|(.*\(low RAM\)) |(.*\(Fail\))', e.response.stdout))[0]) + ' ' + str((re.findall(r'Logfiles stored in .*', e.response.stdout))[0]) + '\n'
            except Exception:
                error_message = "Error running the MoBatch command {0}".format(str(e.response.stdout))
        elif isinstance(e, EnvironWarning):
            warning_message = "{exception}: '{message}'".format(exception=e.__class__.__name__, message=str(e)[:error_length])
        else:
            if isinstance(e, NoNodesAvailable):
                self.no_nodes_available = e.message
            error_message = "{exception}: '{message}'".format(exception=e.__class__.__name__, message=str(e)[:error_length])

        if error_message:
            # Updates error message if truncated
            error_message = self.update_error(e, error_length, error_message)
            self._persist_error_or_warning_as_string(error_message, self._profile_error_key, error_type=error_type)
        else:
            warning_message = self.update_error(e, error_length, warning_message)
            self._persist_error_or_warning_as_string(warning_message, self._profile_warning_key, error_type=error_type)

    def update_error(self, e, error_length, err_msg):
        """
        Used to return the error message whether truncated or not
        :param e: Exception
        :type e: Exception
        :param error_length: error length w.r.t different exceptions
        :type error_length: Integer
        :param err_msg: Error message
        :type err_msg: String
        :return: Returns the error message after truncation is done
        :rtype: String
        """
        if self.NAME in ["HA_01", "APT_01"]:
            team = "BumbleBee" if self.NAME in ["APT_01"] else "BRAVO"
            allocation_note = (" Due to NRM constraints not all nodes are expected to be available for "
                               "HA_01." if team == "BRAVO" else "")
            err_msg = "PLEASE CONTACT TEAM {0} FOR QUERIES IN RELATION TO THIS PROFILE.{1} {2}".format(
                team, allocation_note, err_msg)
        error_message = (err_msg + "...truncated output. See ENM application log on server for more details" if
                         len(str(e)) > error_length else err_msg)
        return error_message

    def _persist_error_or_warning_as_string(self, error_message, profile_key,
                                            error_type=ProfileError().__class__.__name__):
        """
        Stores information on things that went wrong in persistence. This is used for printing workload status

        :type error_type: str
        :param error_type: ProfileError().__class__.__name__
        :type error_message: str
        :param error_message: information on the error that occurred in persistence
        :type profile_key: type of persistence key
        :param profile_key: self._profile_warning_key or self._profile_error_key
        """
        total_number_to_keep = 5
        error = "[{0}] {1}".format(error_type, error_message)
        results = persistence.get(profile_key) or []
        self.check_for_repeating_error(results, error)
        persistence.set(profile_key, results[-total_number_to_keep:], -1, log_values=False)
        log.logger.debug("{0}".format("|".join(error.split("\n"))))
        self.logger.error(' '.join(error.splitlines()))

    def check_for_repeating_error(self, results, error):
        """
        Stacks errors in the results dict if needed. Modify the DUPLICATES list if needed.
        :type error: str
        :param error: latest error thrown.
        :type results: list
        :param results: existing errors in persistence
        """
        if len(results) == 0:
            results.append({"TIMESTAMP": timestamp.get_human_readable_timestamp(), "REASON": error, "DUPLICATES": []})
        else:
            error_matched = False
            for i, existing_error in enumerate(results):
                if re.sub("[0-9]+", "NUM", error) == re.sub("[0-9]+", "NUM", existing_error["REASON"]):
                    self.logger.debug("Duplicate Error found")
                    # Pop that index and append to the end.
                    popped_error = results.pop(i)
                    old_timestamp = existing_error["TIMESTAMP"]
                    popped_error["TIMESTAMP"] = timestamp.get_human_readable_timestamp()
                    popped_error["REASON"] = error
                    if "DUPLICATES" not in popped_error:
                        popped_error["DUPLICATES"] = []
                    popped_error["DUPLICATES"].append(old_timestamp)
                    popped_error["DUPLICATES"] = popped_error["DUPLICATES"][-5:]
                    results.append(popped_error)
                    error_matched = True
                    break
            if not error_matched:
                # No match found, create new error
                results.append({"TIMESTAMP": timestamp.get_human_readable_timestamp(), "REASON": error, "DUPLICATES": []})
                self.logger.info("No Match found....new error added")

    def clear_errors(self):
        """
        Removes information on all errors for the profile. Done by "workload clear_error"
        """
        persistence.remove(self._profile_error_key)
        persistence.remove(self._profile_warning_key)

    def remove(self):
        """
        Removes all references to the profile object in persistence. Done after a teardown
        """
        persistence.remove(self.NAME)
        persistence.remove('{0}-status'.format(self.NAME))
        persistence.remove('{0}-diff'.format(self.NAME))
        self.clear_errors()
        # Change to use persistence backed blocking list
        with mutexer.mutex("workload_profile_list", persisted=True):
            active_profiles = persistence.get("active_workload_profiles")
            try:
                active_profiles.remove(self.NAME)
                persistence.set("active_workload_profiles", active_profiles, -1)
            except ValueError:
                pass

    def teardown(self, remove=False):
        """
        Invokes the _teardown method on all objects that have been added to the teardown list and removes
        the object from persistence

        :type remove: bool
        :param remove: flags whether to remove profile from persistence or not
        """

        log.logger.debug("Starting TEARDOWN")
        if self.state in ['RUNNING', 'STARTING', 'SLEEPING']:
            self.logger.error("Profile state DEAD")
        time.sleep(self.THREADING_TEARDOWN_TIMER)  # For multi-threaded teardown

        node_mgr = nodemanager_adaptor if self.nodemanager_service_can_be_used else node_pool_mgr

        try:
            teardown_list = self.teardown_list
            for _ in range(len(teardown_list)):
                self.teardown_items(teardown_list)
            if (not (self.EXCLUSIVE or self.is_completed or getattr(self, 'RETAIN_NODES', False)) and
                    (hasattr(self, 'NUM_NODES') or hasattr(self, 'TOTAL_NODES') or hasattr(self, 'NODES')) and
                    not self.no_nodes_available):
                log.logger.debug("Node deallocation started")
                node_mgr.deallocate_nodes(self)
                log.logger.debug("Node deallocation complete")
            else:
                log.logger.info('{0} is either EXCLUSIVE or does not handle nodes. '
                                'To release nodes from exclusive profiles, run: '
                                '"workload stop {0} --release-exclusive-nodes"'
                                .format(self.NAME))
        finally:
            self.user_cleanup()
            if remove:
                self.remove()
            process.kill_spawned_process(self.NAME, self.pid)

        log.logger.debug("TEARDOWN Finished")

    def teardown_items(self, teardown_list):
        """
        Calls the _teardown method on all objects that have been added to the teardown list

        :type teardown_list: list
        :param teardown_list: List of teardown items
        """
        try:
            teardown_item = teardown_list.pop()
            if callable(teardown_item):
                teardown_item()
            else:
                teardown_item._teardown()
        except Exception as e:
            log.logger.debug(str(e))
            if "401" in str(e) and hasattr(teardown_item, 'user'):
                teardown_item.user = get_workload_admin_user()
                if callable(teardown_item):
                    teardown_item()
                else:
                    teardown_item._teardown()

    def process_user_request_errors(self, users):
        """
        Aggregates information on rest requests and their responses made by users in UI Profiles

        :type users: enm_user_2.User object
        :param users: users with user.ui_response_info values to aggregate
        """
        responses = defaultdict(list)
        updated_body = None
        for user in users:
            for request, response_info in user.ui_response_info.iteritems():
                responses[request].append(response_info)
            user.ui_response_info = defaultdict(dict)

        for request, response_info in responses.iteritems():
            # Check for any invalid responses
            if any([item[False] for item in response_info]):
                total_fails = sum([item[False] for item in response_info])
                total_responses = total_fails + sum([item[True] for item in response_info])
                sample_error = random.choice([item for item in response_info if item[False]])["ERRORS"].values()[0]

                if hasattr(sample_error, "text"):
                    updated_body = self._extract_html_text(sample_error.text)

                error_message = 'Failed to "{0}" at "{1}", {2}/{3} times.\n' \
                                'Sample Status Code: {4}\n' \
                                'Sample Response: {5}' \
                                ''.format(request[0], request[1], total_fails, total_responses,
                                          sample_error.status_code,
                                          updated_body if updated_body else sample_error.text[:1000])

                self.add_error_as_exception(EnmApplicationError(error_message))

    def process_thread_queue_errors(self, tq, last_error_only=False):
        """
        Process the thread queue errors, and count the number of errors encountered

        :param tq: thread queue to process
        :type tq: thread_queue.ThreadQueue object
        :param last_error_only: if True only add the last error in the list of tq exceptions as an exception
        :type last_error_only: Boolean
        :return: number fo exceptions encountered by the Thread Queue
        :rtype: int

        """
        if last_error_only and tq.exceptions:
            self.add_error_as_exception(tq.exceptions[-1])
        else:
            for exception_msg in tq.exceptions:
                self.add_error_as_exception(exception_msg)

        return len(tq.exceptions)

    @property
    def nodes_list(self):
        """
        Returns list of nodes in workload pool

        :return: List of Node objects
        :rtype: list
        """
        log.logger.debug("Get list of nodes allocated to profile {0} (using full node objects)".format(self.NAME))
        if self.nodemanager_service_can_be_used:
            nodes = nodemanager_adaptor.get_list_of_nodes_from_service(profile=self.NAME)
        else:
            nodes = node_pool_mgr.get_pool().allocated_nodes(self)
        log.logger.debug("Allocated node count (using full node objects): {0}".format(len(nodes)))
        process.get_current_rss_memory_for_current_process()
        return nodes

    def get_nodes_list_by_attribute(self, node_attributes=None, profile_name=None):
        """
        Returns list of nodes in workload pool, with each node object returned having specific attributes only

        :param node_attributes: List of node attributes required per node
        :type node_attributes: list
        :param profile_name: Profile Name
        :type profile_name: str
        :return: List of Node objects
        :rtype: list
        """
        profile_name = profile_name or self.NAME
        log.logger.debug("Get list of nodes allocated to profile {0} (using specific node attributes)"
                         .format(profile_name))
        if self.nodemanager_service_can_be_used:
            nodes = nodemanager_adaptor.get_list_of_nodes_from_service(profile=profile_name,
                                                                       node_attributes=node_attributes)
        else:
            nodes = node_pool_mgr.get_allocated_nodes(profile_name, node_attributes=node_attributes)
        log.logger.debug("Allocated node count (using specific node attributes): {0}".format(len(nodes)))
        process.get_current_rss_memory_for_current_process()
        return nodes

    def all_nodes_in_workload_pool(self, node_attributes=None, is_num_nodes_required=True):
        """
        Returns all nodes from the workload pool

        :param node_attributes: List of node attributes to be included
        :type node_attributes: list
        :param is_num_nodes_required: it skips NUM_NODES nodes filter, when is_num_nodes_required is False.
        :type is_num_nodes_required: boolean

        :return: node list
        :rtype: list
        """
        process.get_current_rss_memory_for_current_process()
        log.logger.debug("Fetching all nodes in workload pool")
        if self.nodemanager_service_can_be_used:
            nodes = nodemanager_adaptor.get_list_of_nodes_from_service(node_attributes=node_attributes)
            log.logger.debug("Nodes returned by service: {0}".format(len(nodes)))
            if hasattr(self, "NUM_NODES") and is_num_nodes_required:
                log.logger.debug("Filtering nodes by type in NUM_NODES: {0}".format(self.NUM_NODES))
                nodes = [node for node in nodes
                         if hasattr(node, "primary_type") and node.primary_type in self.NUM_NODES.keys()]
                log.logger.debug("Number of nodes after filtering: {0}".format(len(nodes)))
        else:
            nodes = node_pool_mgr.get_all_nodes_using_separate_process(self, node_attributes=node_attributes)

        process.get_current_rss_memory_for_current_process()
        return nodes

    def get_all_nodes_in_workload_pool_based_on_node_filter(self):
        """
        Returns all nodes from the workload pool that match the managed_element_type given in NODE_FILTER

        :return: node list
        :rtype: list
        """
        nodes_list = self.all_nodes_in_workload_pool(node_attributes=['node_id', 'managed_element_type', 'poid',
                                                                      'primary_type'])
        all_managed_elements_types = [managed_element.get('managed_element_type') for managed_element in
                                      self.NODE_FILTER.values() if managed_element]
        managed_elements_types = [elements for elements in all_managed_elements_types[0]]
        log.logger.debug("managed_elements list {0}".format(managed_elements_types))
        profile_nodes = [node for node in nodes_list if node.managed_element_type in managed_elements_types]
        return profile_nodes

    def __str__(self):
        return self.NAME

    def create_users(self, number, roles, fail_fast=True, safe_request=False, retry=False):
        """
        Invokes the user creation operation

        :type number: int
        :param number: number of users to create
        :type roles: list
        :param roles: list of roles to give to users
        :type fail_fast: bool
        :param fail_fast: exit execution if user fails to create
        :type safe_request: bool
        :param safe_request: Ignore certain requests exceptions
        :type retry: bool
        :param retry: retry until a user is created

        :return: list of enm_user objects
        :rtype: list
        :raises EnmApplicationError: if error creating user and fail_fast is True

        """

        users_list, failed_users = [], []
        if usermanager_adaptor.check_if_service_can_be_used_by_profile(profile=self):
            users_list = usermanager_adaptor.create_users_via_usermanager_service(self.NAME, number, roles)
        else:
            log.logger.debug("Using legacy architecture to create users")
            while not users_list:
                users_list, _ = common_utils.create_users_operation(
                    self.identifier, number, roles, fail_fast=fail_fast, safe_request=safe_request, retry=retry)

        failed_users = number - len(users_list)

        if failed_users:
            self.add_error_as_exception(EnmApplicationError("Failed to create {0} users. {1} load will now only run "
                                                            "with {2}/{3} users.".format(failed_users, self.NAME,
                                                                                         len(users_list), number)))
        self.user_count += len(users_list)
        return users_list

    def get_last_run_time(self):
        return self._last_run if self._last_run else self.start_time

    def keep_running(self):
        """
        Returns whether a while loop should continue or complete after one iteration
        :rtype bool
        """
        global _loop_generator
        if not _loop_generator:  # If instance of generator doesn't exist create it
            _loop_generator = self._keep_running()
        return _loop_generator.next()

    def _keep_running(self):
        """
        Generator which yields whether a profile should continue or not
        :rtype bool
        """
        global _loop_generator
        global _iteration_number
        _iteration_number = 0

        if not self.KEEP_RUNNING:  # Runs the loop once then goes to completed
            _iteration_number += 1
            yield True
            _loop_generator = None
            yield self.KEEP_RUNNING  # False
        elif isinstance(self.KEEP_RUNNING, int) and not isinstance(self.KEEP_RUNNING, bool):
            # Runs the loop certain number of times then goes to completed
            for _ in xrange(0, self.KEEP_RUNNING):
                _iteration_number += 1
                yield True
            _loop_generator = None
            yield False
        else:
            while True:  # Returns True always. Case for profiles we want to continue forever
                yield self.KEEP_RUNNING  # True

    def get_schedule_times(self):
        """
        If the profile has the SCHEDULED_TIMES_STRINGS returns a list of datetimes.
        :return: list of datetimes
        :rtype: list

        """
        scheduled_times = []
        now = datetime.datetime.now()
        for t in self.SCHEDULED_TIMES_STRINGS:
            dt = datetime.datetime.strptime(t, "%H:%M:%S")
            s_time = now.replace(hour=dt.hour, minute=dt.minute, second=dt.second)
            log.logger.debug("{}".format(s_time))
            scheduled_times.append(s_time)

        return scheduled_times

    def _log_after_completed(self):
        """
        Logs every 24 hours after going to completed

        """
        while self.state == 'COMPLETED':
            msg = "Profile has COMPLETED." or self.no_nodes_available
            self.logger.info(msg)
            time.sleep(86400)  # Using self.sleep() will log the sleep and add to the teardown

    def sleep_during_upgrade_run(self):
        """
        Checks for 'upgrade_run' key in persistence db, sets profile's state to 'SLEEPING' if True

        """
        profiles_to_sleep = ['CMEXPORT_03', 'CMEXPORT_11', 'CMIMPORT_08', 'AMOS_01', 'NETEX_01', 'ENMCLI_01', 'FMX_01',
                             'PLM_01', 'ESM_01', 'GEO_R_01', 'NODESEC_11', 'NODESEC_13']
        if self.NAME in profiles_to_sleep:

            while True:
                upgrade_run = persistence.get("upgrade_run")
                if upgrade_run is not None and upgrade_run.title() == 'True':
                    # wait for upgrade to complete
                    self.state = 'SLEEPING'
                    log.logger.debug("SLEEPING for 5 mins as the 'upgrade_run' flag has been enabled in persistence")
                    time.sleep(300)
                else:
                    break

    def _log_when_sleeping_for_gt_four_hours(self, duration):
        """
        Log to daemon log if sleeping for more than four hours

        :param duration: NUmber of seconds to sleep
        :type duration: int
        """
        duration_of_4hrs = 60 * 60 * 4

        count = 0
        while duration > duration_of_4hrs:
            if not count:
                self.state = SLEEPING
            count += 1
            time.sleep(duration_of_4hrs)
            duration -= duration_of_4hrs

        if duration > 0:
            if count:
                log.logger.debug("Sleeping for remaining time: {0}s".format(duration))
            time.sleep(duration)

        self.sleep_during_upgrade_run()

    def sleep_until_next_scheduled_iteration(self):
        """
        Sleeps until the next expected iteration time based on the "SCHEDULED.*" inputs in the profile values
        within the network files

        """
        log.logger.debug("Attempting to sleep until the profiles next scheduled iteration.")

        if hasattr(self, "SCHEDULED_DAYS"):
            self.sleep_until_day()
        elif hasattr(self, "SCHEDULED_TIMES_STRINGS"):
            self.sleep_until_time()
        else:
            self.sleep()

        log.logger.debug("Successfully slept until the profiles next scheduled iteration.")

    def user_cleanup(self):
        """
        Queries ENM for all users, and then attempts to delete all profile users
        """
        if getattr(self, "user_count", 0):
            if usermanager_adaptor.check_if_service_can_be_used_by_profile(self):
                usermanager_adaptor.delete_users_via_usermanager_service(self.NAME)

            else:
                log.logger.debug("Using legacy architecture to delete users")
                common_utils.delete_profile_users(self.NAME)
        else:
            log.logger.debug("Profile does not have user count value, so no users to be removed from ENM")

    def check_if_error_limit_reached(self):
        """
        Check if the error has pushed the daily count over the limit

        :return: If the error logging limit has been reached
        :rtype: bool
        """
        self.daily_error_count += 1
        if self.daily_error_count > self.ERROR_LIMIT:
            if not self.logged_exceeded_limit_message:
                log.logger.debug('Profile has exceeded error logging limit of {0} '
                                 'for today: {1}'.format(self.ERROR_LIMIT, self.reset_date))
                self.logged_exceeded_limit_message = True
            return not self.reset_error_counter()

    def reset_error_counter(self):
        """
        Reset the daily counter if a new day.

        :return: If the counter has been reset
        :rtype: bool
        """

        current_date = datetime.datetime.now().strftime("%d/%m/%Y")
        if self.reset_date != current_date:
            log.logger.debug("Resetting profiles error limit")
            self.daily_error_count = 0
            self.reset_date = current_date
            self.logged_exceeded_limit_message = False
            return True


class CMImportProfile(Profile):

    def _check_if_allocated_nodes_exceeds_total_nodes(self, nodes_list):
        """
        If the number of nodes in the allocated nodes list exceeds the total nodes required by the profile,
        remove this number of excess nodes from the profile
        """
        log.logger.debug('Check if the number of allocated nodes excess the total nodes required by the profile')
        if hasattr(self, "NUM_NODES") and len(self.NUM_NODES) == 1 and self.NUM_NODES.values()[0] == -1:
            log.logger.debug("The profile requires all available nodes of type {0}.".format(self.NUM_NODES.keys()))
        else:
            total_nodes = self.TOTAL_NODES
            if len(nodes_list) > total_nodes:
                num_excess_nodes = len(nodes_list) - total_nodes
                log.logger.debug(
                    'The number of nodes allocated to the profile exceeds the number of nodes required by the profile. '
                    'The excess number of nodes ({0}) will be removed from the profile'.format(num_excess_nodes))
                list_to_remove = nodes_list[:num_excess_nodes]
                log.logger.debug('Removing {0} nodes from the Profile. '.format(num_excess_nodes))
                SHMUtils.deallocate_unused_nodes(list(list_to_remove), self)
                for node in list_to_remove:
                    nodes_list.remove(node)
                self.persist()
                log.logger.debug('Successfully removed {0} nodes'.format(list_to_remove))

    @property
    def nodes_list(self):
        nodes_list = self.get_nodes_list_by_attribute(['node_id', 'subnetwork_id', 'subnetwork',
                                                       'mos', 'profiles', 'node_version'])
        mos = persistence.get('%s-mos' % self.NAME)
        num_nodes_to_check = len(nodes_list)
        if nodes_list and mos:
            while num_nodes_to_check > 0:
                for node in nodes_list:
                    num_nodes_to_check -= 1
                    try:
                        node.mos = mos[node.node_id]
                    except KeyError:
                        log.logger.debug('Node {0} is not in the persisted list of nodes with MOs and will be '
                                         'removed from the nodes list'.format(node))
                        nodes_list.remove(node)
            self._check_if_allocated_nodes_exceeds_total_nodes(nodes_list)
        else:
            self.state = "COMPLETED"
            raise EnvironError('Nodes with required MOs must be provided to create import')

        return nodes_list

    def run(self):
        raise NotImplementedError("No run method defined")


class ExclusiveProfile(CMImportProfile):
    NODE_VERSION = None
    NODES_PER_HOST = None

    def __init__(self, name):
        log.logger.debug("Creating Exclusive Profile for {0} ".format(name))
        self.NAME = name
        super(ExclusiveProfile, self).__init__()

    @property
    def used_nodes(self):
        """
        Property to get the list of nodes used by the profile
        """
        if self.nodemanager_service_can_be_used:
            return [node for node in nodemanager_adaptor.get_list_of_nodes_from_service()
                    if bool(node.profiles) and node.is_exclusive]
        else:
            return [node for node in node_pool_mgr.get_pool().nodes if node.used and node.is_exclusive]

    @property
    def nodes_list(self):
        if 'CM' in self.NAME:
            return super(ExclusiveProfile, self).nodes_list
        return [node for node in self.used_nodes if self.NAME in node.profiles]

    @property
    def application(self):
        return self.NAME.split('_')[0]

    def run(self):
        pass

    @property
    def currently_allocated_nodes(self):
        """
        Retrieve the list of nodes currently allocated to the profile

        :return: List of currently allocated nodes
        :rtype: list
        """
        log.logger.debug("Checking for nodes currently allocated to profile: {0}".format(self.NAME))
        if self.nodemanager_service_can_be_used:
            return nodemanager_adaptor.get_list_of_nodes_from_service(profile=self.NAME)
        else:
            return node_pool_mgr.get_pool().allocated_nodes(self)


class DiffProfile(object):

    def __init__(self, **kwargs):
        self.NAME = kwargs.pop('name')
        self.start_time = kwargs.pop('start_time')
        self.version = kwargs.pop('version')
        self.update_version = kwargs.pop('update_version')
        self.state = kwargs.pop('state')
        self.supported = kwargs.pop('supported')
        super(DiffProfile, self).__init__()


class TeardownList(list):
    def __init__(self, profile, *args):
        """
        TeardownList constructor

        :type profile: enmutils_int.lib.Profile
        :param profile: Profile object to persist
        :type args: list
        :param args: list of args
        """
        list.__init__(self, *args)
        self.profile = profile

    def append(self, item):
        """
        Appends item to list and persists the profile
        """

        if item:
            log.logger.debug("APPENDING item: {0} to the teardown list".format(item))
            super(TeardownList, self).append(item)
            if hasattr(self, "profile"):
                self.profile.persist()
        else:
            log.logger.debug("Tried to add None object to the teardown list.")


def set_script_engine_error(e):
    """
    Updates the message based on the supplied exception

    :param e: Exception to be edited
    :type e: `exceptions.EnmApplicationError`

    :return: Updated error message based on the supplied exception object
    :rtype: str
    """
    try:
        output = "\n".join(line for line in e.response.get_output() if line)
        error_message = ("ScriptEngineError: Command: '{command}'\nResponse: '{response}'\nError Message: '{message}'"
                         .format(command=e.response.command[:700], response="{}....{}".format(output[:200],
                                                                                              output[:200]),
                                 message=e.message[:200]))
    except Exception:
        error_message = "{exception}: '{message}'".format(exception=e.__class__.__name__, message=str(e))
    return error_message


def set_connection_error(e, exception_msg):
    """
    Updates the message based on the supplied exception

    :param e: Exception to be edited
    :type e: `exceptions.ConnectionError`
    :param exception_msg: The exception message value
    :type exception_msg: str

    :return: Updated error message based on the supplied exception object
    :rtype: str
    """
    method = e.request.method if e.request and hasattr(e.request, 'method') else None
    url = e.request.url[:500] if e.request and hasattr(e.request, 'url') else None
    base_msg = "ConnectionError: '{method}' request to {request} raised ConnectionError {exception}. No response given."
    l_msg = ("The REST call is terminated as the associated ENM service didn't respond within httpd's timeout threshold"
             " of 2 minutes.\n{0}".format(base_msg.format(method=method, request=url, exception=str(e))))
    if "Connection aborted" in exception_msg:
        error_message = l_msg
    else:
        error_message = base_msg.format(method=method, request=url, exception=str(e))
    return error_message


def set_http_error(e, exception_msg):
    """
    Updates the message based on the supplied exception

    :param e: Exception to be edited
    :type e: `exceptions.ConnectionError`
    :param exception_msg: The exception message value
    :type exception_msg: str

    :return: Updated error message based on the supplied exception object
    :rtype: str
    """
    updated_body = None
    error_message = str(e)
    filename_msg = "Removed request body, as filename= found in response"
    try:
        if hasattr(e.response.request, "text"):
            updated_body = extract_html_text(str(e.response.request.body))
        payload = ("\nPayload: {0}".format(str(e.response.request.body)[:700])
                   if hasattr(e.response.request, "body") and "filename=" not in str(e.response.request.body)
                   else filename_msg if (hasattr(e.response.request, "body") and
                                         "filename=" in str(e.response.request.body)) else "")
        text = updated_body if updated_body else e.response.text[:2000]
        if "Connection aborted" in exception_msg:
            error_message = ("The REST call is terminated as the associated ENM service didn't respond within httpd's "
                             "timeout threshold of 2 minutes.\nHTTPError: '{method}' request to {request} failed with "
                             "status code: {status_code}{payload}\nResponse: {text}"
                             .format(method=e.request.method, request=e.response.request.url[:500],
                                     status_code=e.response.status_code, text=text, payload=payload))
        else:
            error_message = ("HTTPError: '{method}' request to {request} failed with status code: {status_code}"
                             "{payload}\nResponse: {text}"
                             .format(method=e.request.method, request=e.response.request.url[:500],
                                     status_code=e.response.status_code, text=text, payload=payload))
        return error_message
    except Exception as err:
        return str(err)


def extract_html_text(html_body):
    """
    Extract text from html

    :type html_body: str
    :param html_body: Html file to extract info from
    :rtype: str
    :return: result of extracted text
    """
    result = html_body
    if "<html>" in html_body:
        try:
            if "JBWEB" in html_body:
                title_regex = r"<title>(.+?)</title>"
                description_regex = r"<u>(JBWEB.+?)</u>"
                title_result = re.search(title_regex, html_body)
                description_result = re.search(description_regex, html_body)

                if title_result and description_result:
                    result = "[JBOSS] %s%s" % (title_result.group(1), description_result.group(1))
            else:
                parsed = re.sub(r"\|+", "|", re.sub(r"<[^<]+?>", "|||", html_body))[1:-1].split("|")
                result = "[HTML] " + " >> ".join([text for text in parsed if text.strip()])
        except Exception as e:
            log.logger.debug("Exception while extracting text from html: {0}".format(str(e)))
    return result
