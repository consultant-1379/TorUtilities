# ********************************************************************
# Name    : Workload Ops
# Summary : Core functionality of the workload tool. Responsible for
#           all areas of the workload tool operations, except node
#           operations such as add, remove and reset. Manages the
#           start, restart, stop, list, diff, export, describe,
#           status and other informational operations.
# ********************************************************************

import commands
import datetime
import json
import os
import re
import signal
from collections import defaultdict
from textwrap import TextWrapper

from tabulate import tabulate

from enmutils.lib import log, persistence, mutexer, cache, shell, config, process
from enmutils.lib.cache import is_enm_on_cloud_native, is_host_physical_deployment
from enmutils.lib.enm_user_2 import User
from enmutils.lib.exceptions import EnvironError, ProfileError, EnmApplicationError, NetsimError
from enmutils.lib.thread_queue import ThreadQueue
from enmutils_int.bin.network import network_health_check
from enmutils_int.lib import (load_mgr, node_pool_mgr, workload_schedule,
                              common_utils, profile_properties_manager, profile_manager)
from enmutils_int.lib.common_utils import (remove_profile_from_active_workload_profiles,
                                           add_profile_to_active_workload_profiles)
from enmutils_int.lib.services import deployment_info_helper_methods
from enmutils_int.lib.services import (nodemanager_adaptor, profilemanager_adaptor, profilemanager,
                                       profilemanager_helper_methods, nodemanager_helper_methods)
from enmutils_int.lib.services.deploymentinfomanager_adaptor import (check_enm_access,
                                                                     check_password_ageing_policy_status)
from enmutils_int.lib.services.usermanager_adaptor import get_profile_sessions_info
from enmutils_int.lib.workload_network_manager import InputData

IMPORT_URL = "https://eteamspace.internal.ericsson.com/pages/viewpage.action?pageId=2049928279"
APT_URL = "https://eteamspace.internal.ericsson.com/display/ERSD/Starting+APT_01"
STOP_CMD_THREAD_TIMEOUT = 3600 * 3
DEPENDENT_SERVICES = ["crond", "rsyslog", "ddc", "deploymentinfomanager", "nodemanager", "profilemanager",
                      "usermanager"]
SERVICES_NOT_RUNNING = []


class WorkloadInfoOperation(object):
    def __init__(self, profile_names=None, restart=None):
        """
        Basic workload operation class from which other specialised classes are derived
        """
        self.profile_objects = None
        self.active_profiles = None
        self.status_profiles = None
        self.supported_profiles = None
        self.profile_names = [profile.upper() for profile in profile_names] if profile_names else []
        self.total_nodes = 0
        self.restart = restart
        self.priority = None
        self.nodemanager_service_to_be_used = False
        self.print_summary = True
        self.base_profile_log_path = os.path.join(config.get_log_dir(), "daemon/{0}.log")
        self.operation_type = None
        tab = __import__("tabulate")
        tab.MIN_PADDING = 0

    def _validate(self):
        raise NotImplementedError("This method should be overridden by the derived class")

    def _setup(self):
        if not self.nodemanager_service_to_be_used and nodemanager_adaptor.can_service_be_used():
            log.logger.debug("Using nodemanager services for node queries")
            self.nodemanager_service_to_be_used = True

        if self.operation_type != "start":
            self._update_total_node_count(update=False)
        self.supported_profiles = profilemanager_helper_methods.get_all_profile_names()

    def _update_total_node_count(self, update=True):
        """
        Update the total node count if required

        :param update: Boolean indicating if the default behaviour is to update the value
        :type update: bool
        """
        if self.nodemanager_service_to_be_used:
            if not isinstance(self, ListNodesOperation):
                self.total_nodes, _, _ = nodemanager_adaptor.list_nodes()
        else:
            self.total_nodes = nodemanager_helper_methods.update_total_node_count(update=update)

    def execute(self):

        self._setup()
        self._execute_operation()

    def _execute_operation(self):
        """
        Executes command
        """

        raise NotImplementedError("This method should be overridden by the derived class")

    def _set_active_profiles(self, specific_profiles=None):
        """
        Sets the active_profiles attribute with a list of profiles currently active

        :param specific_profiles: a list of specific profiles to check if they are active.
        :type specific_profiles: list
        """

        self.profile_objects = load_mgr.get_persisted_profiles_by_name(profile_names=specific_profiles)
        # If specific_profiles specified
        if specific_profiles:
            active_profiles = {profile_name: profile for profile_name, profile in self.profile_objects.iteritems() if
                               profile_name in specific_profiles}
        else:
            active_profiles = {profile_name: profile for profile_name, profile in self.profile_objects.iteritems() if
                               profile}

        self.active_profiles = active_profiles

    def _set_active_status(self, specific_profiles=None, json_response=False):
        """
        Sets the active status' of profiles currently active

        :param specific_profiles: a list of specific profiles to check if they are active.
        :type specific_profiles: list
        :param json_response: Boolean to indicate format of data to be returned
        :type json_response: bool
        :return: list of active profiles
        :rtype: list
        """
        if not profilemanager_adaptor.can_service_be_used():
            active_status_profiles = load_mgr.get_persisted_profiles_status_by_name(
                self.priority, profile_names=specific_profiles) or []
            if specific_profiles and active_status_profiles:
                self.status_profiles = [profile for profile in active_status_profiles if
                                        profile.NAME in specific_profiles]
            else:
                self.status_profiles = active_status_profiles
        else:
            profiles_found = profilemanager_adaptor.get_status({'profiles': specific_profiles,
                                                                "json_response": json_response})
            self.filter_profiles_status_based_on_priority_and_json_response(profiles_found, json_response)

        return self.status_profiles

    def filter_profiles_status_based_on_priority_and_json_response(self, profiles_found, json_response):
        """
        Filters the profiles status from profiles_found based on priority.
        Set the profiles status(json format) to self.status_profiles, if json response is true,
        Otherwise set the profiles status(profile Objects) to self.status_profiles

        :param profiles_found: List of status_profiles
        :type profiles_found: list
        :param json_response: Boolean to indicate format of data to be returned
        :type json_response: bool
        """
        if json_response:
            self.status_profiles = (profiles_found if not self.priority else
                                    [profile for profile in profiles_found
                                     if profile['priority'] == int(self.priority)])
        else:
            self.status_profiles = (profiles_found if not self.priority else
                                    [profile for profile in profiles_found if profile.priority == int(self.priority)])


class WorkloadOperation(WorkloadInfoOperation):
    def __init__(self, profile_names=None, restart=None):
        """
        An extension of the basic workload class that includes the setting of active profiles and supported profile
        names in its setup

        :param profile_names: The names of specific profiles that this operation applies to
        :type profile_names: list
        :param restart: Flag controlling restart
        :type restart: bool
        """

        super(WorkloadOperation, self).__init__(profile_names, restart=restart)

    def _validate(self):
        """
        Overrides parent function
        """

    def _setup(self):
        """
        Performs some operations common to most SubClasses
        """
        if getattr(self, 'initial_install_teardown', False):
            return
        super(WorkloadOperation, self)._setup()
        self._set_active_profiles(specific_profiles=self.profile_names)

        if not self.restart:
            self._remove_none_type_profiles()
        self._validate()

    def _remove_none_type_profiles(self):
        """
        Temporary workaround before we figure out why None profiles are found in persistence
        daemon is usually running
        """

        none_type_profiles = []

        if self.profile_objects:
            for profile_name, profile_obj in self.profile_objects.iteritems():
                if not profile_obj:
                    none_type_profiles.append(profile_name)

            # Figure out why profiles get persisted as None and come up with a better solution
            if none_type_profiles:
                log.logger.warn(
                    "ERROR: Profile(s) {0} are no longer in persistence.".format(",".join(none_type_profiles)))
                log.logger.warn(
                    "Please run 'ps -ef | grep -i <profile_name>' to check if profile process is still running")
                log.logger.warn("If process is running - it should eventually re-persist itself.")
                with mutexer.mutex("workload_profile_list", persisted=True):
                    running_now = persistence.get("active_workload_profiles")
                    for profile_name in none_type_profiles:
                        if profile_name in self.active_profiles:
                            self.active_profiles.pop(profile_name)
                        if profile_name in running_now:
                            running_now.remove(profile_name)
                        persistence.remove(profile_name)
                    persistence.set("active_workload_profiles", running_now, -1)

    def _execute_operation(self):
        """
         Executes command
         """

        raise NotImplementedError("This method should be overridden by the derived class")


class WorkloadHealthCheckOperation(WorkloadOperation):
    def __init__(self, health_check=False, no_exclusive=False, restart=None, no_network_size_check=False):
        """
        Performs a network.network_health_check() prior to execution
        """

        super(WorkloadHealthCheckOperation, self).__init__(restart=restart)
        self.health_check = health_check
        self.no_exclusive = no_exclusive
        self.no_network_size_check = no_network_size_check

    def _validate(self):
        pass

    def _setup(self):
        super(WorkloadHealthCheckOperation, self)._setup()

        if self.health_check:
            network_health_check()
            try:
                profilemanager_helper_methods.report_syncronised_level()
            except Exception as e:
                log.logger.error("Unable to get network status, error countered:: [{0}]. "
                                 "ENM may be experiencing problems.".format(str(e)))

    def _execute_operation(self):
        """
         Executes command
         """

        raise NotImplementedError("This method should be overridden by the derived class")

    def _allocate_exclusive_nodes(self, profile_list, service_to_be_used):
        """
        Method to allocate exclusive nodes and set the key in persistence
        """
        log.logger.debug("Allocation of nodes to exclusive profiles (if applicable)")
        if not self.no_exclusive and 'EXCLUSIVE-ALLOCATED' not in persistence.get_all_keys():
            log.logger.debug("Get all exclusive profiles")
            exclusive_profiles = InputData().get_all_exclusive_profiles

            log.logger.debug("Exclude unsupported exclusive profiles")
            exclude = [profile for profile in profile_list if profile in exclusive_profiles]
            exclude.extend(self._exclude_unsupported_exclusive_profiles(exclusive_profiles))

            log.logger.debug("Allocate nodes to exclusive profiles")
            if load_mgr.allocate_exclusive_nodes(exclude=exclude, service_to_be_used=service_to_be_used):
                log.logger.debug("Set EXCLUSIVE-ALLOCATED in persistence")
                persistence.set('EXCLUSIVE-ALLOCATED', True, -1, log_values=False)

        log.logger.debug("Allocation of nodes to exclusive profiles - complete")

    def _exclude_unsupported_exclusive_profiles(self, exclusive_profiles):
        """
        Exclude any profiles that does not have a valid support type or has supported set to False
        Explanation:
            Exclusive Profiles with SUPPORTED=False may become supported later and will require their nodes then.
            Excluding profiles like APT_01 with SUPPORTED="APT". To start this type of exclusive profile, all
            profiles need to be stopped first.

        :param exclusive_profiles: The current list of exclusive profiles found on this server's network type configuration
        :type exclusive_profiles: list
        :return: An updated list of profiles to exclude
        :rtype: list
        """
        exclude = []
        valid_supported_types = cache.get('valid_supported_types') if cache.has_key('valid_supported_types') else [True]
        profile_objects = profile_properties_manager.ProfilePropertiesManager(
            exclusive_profiles, self.config_file).get_profile_objects()
        for profile in profile_objects:
            if hasattr(profile, "SUPPORTED") and (
                    profile.SUPPORTED not in valid_supported_types and profile.SUPPORTED is not False):
                exclude.append(profile.NAME)
        return exclude


class WorkloadPoolSummaryOperation(WorkloadInfoOperation):
    """
    Prints a summary of the workload pool after the operation is complete
    """

    def _validate(self):
        pass

    def execute(self):

        self._setup()
        self._validate()
        try:
            self._execute_operation()
        except Exception as e:
            log.logger.info(log.red_text(e.message))
            # Required to still raise the exception but not output the message twice
            raise type(e)(e.message.replace(e.message, ""))
        finally:
            if self.print_summary:
                self._print_node_pool_summary()
            log.logger.debug("Operation Completed")

    def _execute_operation(self):
        """
         Executes command
         """

        raise NotImplementedError("This method should be overridden by the derived class")

    def _print_node_pool_summary(self):
        """
        Prints the total number of nodes in the workload pool.
        """
        log.logger.info("{0}".format(log.green_text(log.underline_text("\nNodes Summary\n"))))
        log.logger.info(log.blue_text("  TOTAL NODES FOUND: %d" % self.total_nodes))
        log.logger.info("")


class DisplayProfilesOperation(WorkloadInfoOperation):
    def __init__(self, argument_dict):
        """
        Display existing profiles in order sorted as in 'workload start'
        """

        super(DisplayProfilesOperation, self).__init__()

        self.exclusive_profiles = None
        self.existing_profile_names = None
        self.exclusive = argument_dict['--exclusive'] if argument_dict['--exclusive'] else False

    def _validate(self):
        pass

    def _execute_operation(self):
        """
        Performs the execute operation
        """
        if self.exclusive:
            obj = InputData()
            obj.ignore_warning = True
            self.exclusive_profiles = sorted(obj.get_all_exclusive_profiles)
            self._print_sorted_profile_names()
        else:
            if not profilemanager_adaptor.can_service_be_used():
                self.existing_profile_names = set(profilemanager_helper_methods.get_all_profile_names())
                self._print_sorted_profile_names()
            else:
                profilemanager_adaptor.get_all_profiles_list()

    def _print_sorted_profile_names(self):
        """
        Function to output the profile details.
        """
        if self.exclusive:
            log.logger.info(log.cyan_text('Exclusive Profiles: \n{0}.'.format(log.green_text(
                ', '.join([prof.upper() for prof in self.exclusive_profiles])))))
        else:
            log.logger.info(log.cyan_text('Existing Profiles: {0}.'.format(log.green_text(
                ', '.join([prof.upper() for prof in self.existing_profile_names])))))


class DisplayCategoriesOperation(WorkloadInfoOperation):
    def __init__(self):
        """
        Display existing categories
        """

        super(DisplayCategoriesOperation, self).__init__()

        self.categories = None

    def _validate(self):
        pass

    def _execute_operation(self):
        """
        Executes the display operation
        """
        if not profilemanager_adaptor.can_service_be_used():
            self.categories = profilemanager_helper_methods.get_categories()
            self._print_categories()
        else:
            profilemanager_adaptor.get_categories_list()

    def _print_categories(self):
        log.logger.info(log.green_text('Categories: {0}'.format(', '.join(self.categories))))


class WorkloadDescriptionOperation(WorkloadInfoOperation):

    def _validate(self):
        pass

    def _execute_operation(self):
        """
        Execute the workload description operation
        """
        if not profilemanager_adaptor.can_service_be_used():
            profilemanager.build_describe_message_for_profiles(self.profile_names)
        else:
            profilemanager_adaptor.describe_profiles(self.profile_names)


class ListNodesOperation(WorkloadPoolSummaryOperation):
    def __init__(self, argument_dict):
        """
        Operation object for listing nodes in workload pool.

        :param argument_dict: dict of arguments with user input
        :type argument_dict: dict
        """
        super(ListNodesOperation, self).__init__()
        self.node_patterns = ([pattern for pattern in argument_dict['IDENTIFIER'].split(",")]
                              if argument_dict["IDENTIFIER"] and not argument_dict['IDENTIFIER'].lower() == 'all'
                              else [])
        self.profile_names = ([profile.upper() for profile in argument_dict['--profiles'].split(",")]
                              if argument_dict["--profiles"] else None)
        self.json_response = argument_dict['--json'] if argument_dict['--json'] else False
        self.print_summary = False if self.json_response else True
        self.errored_nodes = argument_dict['--errored-nodes'] if argument_dict['--errored-nodes'] else False
        self.total_errored_nodes = 0
        self.pool = None
        self.all_nodes = None
        self.nodes_from_query = None
        self.node_count_from_query = 0

    def _setup(self):
        super(ListNodesOperation, self)._setup()
        if self.nodemanager_service_to_be_used:
            self.total_nodes, self.node_count_from_query, self.nodes_from_query = nodemanager_adaptor.list_nodes(
                node_attributes=["node_id", "profiles", "node_ip", "mim_version", "simulation"],
                match_patterns=",".join(self.node_patterns), json_response=self.json_response)
        else:
            self.pool = node_pool_mgr.get_pool()
            self.all_nodes = self.pool.nodes
            self.total_nodes = len(self.all_nodes)

    def _validate(self):
        pass

    def _execute_operation(self):
        """
        Prints a list of all the nodes or a specific list of nodes and their properties that are persisted
        """
        if not self.total_nodes:
            log.logger.warn("No nodes found in the pool. Please add nodes to the pool.\n")
            return

        if self.nodemanager_service_to_be_used:

            if self.node_count_from_query:
                if self.json_response:
                    log.logger.info("{0}".format(json.dumps(self.nodes_from_query)))
                else:
                    self._print_list_of_nodes(self.nodes_from_query)
            else:
                self._print_warning_when_no_matching_nodes_found()

        else:
            self._print_node_info_from_pool()

    def _print_node_info_from_pool(self):
        """
        Print node information based on info in Node Pool
        """
        if self.node_patterns:
            nodes_to_list = self.pool.grep(self.node_patterns).values()
        else:
            nodes_to_list = self.all_nodes

        if not nodes_to_list:
            if self.node_patterns:
                self._print_available_node_names()
                self._print_warning_when_no_matching_nodes_found()
        elif self.json_response:
            log.logger.info(self.pool.jsonify(nodes_to_list))
        else:
            self._print_list_of_nodes(nodes_to_list)

    def _print_list_of_nodes(self, nodes_to_list):
        """
        Print list of nodes to console
        """
        log.logger.debug("{0} node(s) to be printed".format(len(nodes_to_list)))
        log.logger.info("")
        valid_nodes = []
        if self.profile_names:
            for value in self.profile_names:
                for node in sorted(nodes_to_list, key=lambda x: x.node_id):
                    if value in node.profiles:
                        valid_nodes.append(node)
                    self.total_nodes = len(valid_nodes)
                self._print_node_information(valid_nodes, value, self.total_nodes)
                valid_nodes = []
        else:
            for node in sorted(nodes_to_list, key=lambda x: x.node_id):
                valid_nodes.append(node)
            self._print_node_information(valid_nodes)

    def _print_warning_when_no_matching_nodes_found(self):
        """
         Prints a warning to indicate no nodes found matching pattern
         """
        log.logger.warn(
            "No nodes found matching the corresponding pattern '{0}'.\n".format(','.join(self.node_patterns)))

    def _print_available_node_names(self):
        """
        Prints a list of available node names
        """

        if self.all_nodes:
            log.logger.info('Nodes available in pool:')
            log.logger.info(', '.join(node.node_id for node in self.all_nodes))

    @staticmethod
    def _print_node_information(nodes, profile=None, total_nodes=None):
        """
        Prints node information in chunks of 5000 nodes.
        :param nodes: The nodes to print the information about
        :type nodes: list of nodes
        :param profile: The profile is passed to filter nodes.
        :type profile: list of profile.
        :param total_nodes: total_nodes is sum of all nodes of particular profile.
        :type total_nodes: int
        """
        str_representation = []
        if profile is None:
            for node in nodes:
                profiles = (log.yellow_text("NONE") if not node.profiles
                            else log.green_text(", ".join(node.profiles).upper()))
                str_representation.append(
                    "{0} {1} {2} {3}\n\tACTIVE PROFILES: {4}\n".format(log.purple_text(node.node_id),
                                                                       log.blue_text(node.node_ip),
                                                                       node.mim_version,
                                                                       node.simulation, profiles))
            log.logger.info(''.join(str_representation))
        else:
            if len(nodes) == 0:
                str_representation.append(log.red_text("No nodes are allocated to given profile {0}".format(profile)))
                log.logger.info(''.join(str_representation))
            else:
                str_representation.append("The Nodes of Given profile {0} are::".format(log.purple_text(profile)))
                log.logger.info(''.join(str_representation))
                str_representation = []
                for node in nodes:
                    str_representation.append("{0}".format(log.blue_text(node.node_id)))
                log.logger.info(','.join(str_representation))
                log.logger.info("NODES COUNT of Profile {0}: {1}".format(profile, total_nodes))

    def _print_node_pool_summary(self):
        """
        Prints a summary of total/available/error nodes in the workload pool
        """
        log.logger.info("{0}".format(log.green_text(log.underline_text("\nNodes Summary\n"))))
        log.logger.info(log.blue_text("  TOTAL NODES FOUND: %d" % self.total_nodes))
        log.logger.info("")


class StatusOperation(WorkloadPoolSummaryOperation):
    ERROR_TYPES = [obj().__class__.__name__ for obj in [NetsimError, EnvironError, EnmApplicationError, ProfileError]]

    @classmethod
    def shorten_error_type_names(cls):
        """
        Will return a dict of supported error types with keys being shortened
        version of error type name.
        :return: supported types names
        :rtype: dict
        """
        return {i.upper().split('ERROR')[0]: i for i in cls.ERROR_TYPES}

    @classmethod
    def is_supported_error_type(cls, pattern):
        """
        Check if a particular string match to supported error type
        :param pattern: str to check against supported error types
        :type pattern: str
        :return: mapped error type or None if not recognized
        :rtype: str
        """
        supported_keys = cls.shorten_error_type_names()
        match = [v for k, v in supported_keys.items() if pattern.upper() in k]
        return match[0] if match else None

    def __init__(self, argument_dict, profile_names=None):
        """
        Prints a status of all the running workload profiles on the system or a specific list of profiles passed in.

        :param profile_names: profile objects from which to extract the printed information
        :type profile_names: list
        :param argument_dict: dict of arguments with user input
        :type argument_dict: dict
        """

        super(StatusOperation, self).__init__()

        self.profile_names = [profile_name.upper() for profile_name in profile_names] if profile_names else []
        self.errors_only = argument_dict['--errors']
        self.warnings = argument_dict['--warnings']
        self.total = abs(int(argument_dict['--total'])) if argument_dict['--total'] else 0
        self.verbose = argument_dict['--verbose']
        self.sort_by_runtime = argument_dict['--lastrun']
        self.error_types = argument_dict['--error-type'].split(",") if argument_dict['--error-type'] else None
        self.num_starting_profiles = 0
        self.num_completed_profiles = 0
        self.num_running_profiles = 0
        self.num_errored_profiles = 0
        self.num_warning_profiles = 0
        self.num_dead_profiles = 0
        self.sessions = None
        self.profiles_to_print = None
        self.profiles_info_table_values = []
        self.errors_info = defaultdict(list)
        self.health_check = argument_dict['--network-check']
        self.priority = argument_dict['--priority']
        self.json_response = argument_dict['--json'] if argument_dict['--json'] else False

    def execute(self):
        """
        Performs the Status Operation execution
        """
        self._setup()
        self._validate()
        try:
            self._execute_operation()
        except Exception as e:
            log.logger.info(log.red_text(e.message))
            # Required to still raise the exception but not output the message twice
            raise type(e)(e.message.replace(e.message, ""))
        finally:
            if not self.json_response:
                self.get_dependent_services_status()
                self.is_password_ageing_enabled()
                self._print_node_pool_summary()
                self.check_count_of_workload_admin_users()
                self.check_if_enm_accessible()

    def _validate(self):
        """
        Validates user input. Displays invalid input to user.
        """

        invalid_errors = []
        valid_errors = []
        if self.error_types:
            for err in self.error_types:
                match = self.is_supported_error_type(err)
                if match:
                    valid_errors.append(match)
                else:
                    invalid_errors.append(err)

            if invalid_errors:
                log.logger.info(log.red_text("Invalid error types: {0}. Try {1}, or shorter "
                                             "version of these - we will try to match it for you"
                                             ".".format(invalid_errors, ', '.join(self.shorten_error_type_names().keys()))))

            self.error_types = valid_errors or None

    def _execute_operation(self):
        """

        Prints out the status of the workload profiles

        """
        is_prof_manager_enabled = profilemanager_adaptor.can_service_be_used()
        if self.json_response and not is_prof_manager_enabled:
            raise RuntimeError('Unable to get workload status in json format due to profilemanager '
                               'service is disabled on workload vm. Start profilemanager service '
                               'and Again try to get workload status.')
        self.profiles_to_print = self._set_active_status(self.profile_names, self.json_response)
        if self.health_check:
            self.perform_health_check()

        if self.priority and not self.profiles_to_print and self.profile_names:
            raise RuntimeError('No active profile(s) running on the system of categories/names provided with '
                               'priority: {0}'.format(self.priority))
        if not self.profiles_to_print and self.profile_names:
            raise RuntimeError('The following profiles are currently not running: {0}'.format(self.profile_names))
        elif not self.profiles_to_print and self.priority:
            raise RuntimeError('No active profile(s) running on the system of this priority: {0}'.format(self.priority))
        elif not self.profiles_to_print:
            raise RuntimeError('No active profile(s) running on the system')

        if self.json_response:
            log.logger.info("{0}".format(json.dumps(self.profiles_to_print, indent=1)))
        else:
            self._sort_profiles()

            self._set_profile_sessions(self.profiles_to_print)

            tq = ThreadQueue(self.profiles_to_print, num_workers=10, func_ref=self.taskset, task_join_timeout=1 * 60,
                             task_wait_timeout=1 * 60, args=[self])

            tq.execute()
            if tq.exception_msgs:
                log.logger.error("An error has occurred, please check the logs for more information.")
            self.print_status_output()

    def print_status_output(self):
        """
        Print the status values to the console

        :raises RuntimeError: raised if there are profiles errors or if there are DEAD profiles
        """
        if not self.errors_only and not self.warnings:
            self._print_profile_info()
            self._print_profile_summary()

        if (self.errors_only or self.verbose or self.warnings) and self.errors_info:
            self._print_error_info()

        if self.num_dead_profiles or self.num_errored_profiles and not self.errors_only:
            raise RuntimeError("One or more profiles are reporting errors. "
                               "Run /opt/ericsson/enmutils/bin/workload status --errors for further information.")
        elif self.num_dead_profiles or self.num_errored_profiles and self.errors_only:
            raise RuntimeError

    @staticmethod
    def perform_health_check():
        """
        Runs the network health check
        """
        try:
            deployment_info_helper_methods.output_network_basic()
        except Exception as e:
            log.logger.debug("Exception raised for InputData: {0}".format(str(e)))
            log.logger.error("Unable to get network status. ENM may be experiencing problems.")
        network_health_check()

    @staticmethod
    def taskset(profile, status_op_obj):
        """
        Taskset to be supplied to the threadqueue operation

        :param profile: Profile to retrieve the statue information of
        :type profile: `lib.profile.Profile`
        :param status_op_obj: StatusOperation object calling the taskset
        :type status_op_obj: `StatusOperation`
        """
        # NB: Profile.status calls daemon_died which calls process.is_pid_running, so we only want to call it once
        profile_status = profile.status
        status_op_obj._update_status_counts(profile=profile, profile_status=profile_status)
        if profile_status in ["WARNING"]:
            state_colour = log.yellow_text
        else:
            state_colour = log.red_text if profile_status in ['ERROR', 'DEAD'] else log.green_text

        no_schedule_text = ("No further iterations of this profile will occur"
                            if profile.state == "COMPLETED" or profile.status == "DEAD" else "")

        with mutexer.mutex("workload_status_table"):
            status_op_obj.profiles_info_table_values.append([
                profile.NAME,
                profile.state,
                state_colour(profile_status),
                profile.start_time if isinstance(profile.start_time, basestring) else profile.start_time.strftime(
                    "%d-%b %H:%M:%S"),
                profile.pid or '-',
                profile.num_nodes,
                getattr(profile, 'user_count', "Not Available"),
                status_op_obj.sessions[profile.NAME],
                profile.priority,
                no_schedule_text or profile.schedule])
        # profile.errors is a property. Every time it is called it will get the value from persistence
        if status_op_obj.error_types:
            errors = status_op_obj._get_errors_by_type(profile.errors)
            warnings = None
        else:
            errors = profile.errors
            warnings = profile.warnings
        if status_op_obj.errors_only or status_op_obj.verbose:
            status_op_obj.add_output_of_errors_or_warnings(profile, errors)
        if status_op_obj.warnings or status_op_obj.verbose:
            status_op_obj.add_output_of_errors_or_warnings(profile, warnings)

    @staticmethod
    def check_count_of_workload_admin_users():
        """
        Logs if multiple workload admins exists at same time i.e. workload_admin_<hostname>
        """
        try:
            log.logger.debug('Checking number of workload administrator users that exist on ENM')
            all_usernames_enm = User.get_usernames()
            workload_admins = [username for username in all_usernames_enm if 'workload_admin_' in username]
            log.logger.debug('Number of workload admins found on ENM: {0}\n'
                             'All usernames found: {1}'.format(len(workload_admins), workload_admins))
            if len(workload_admins) > 1:
                log.logger.info(log.red_text("{0} Workload admins currently detected on ENM".format
                                             (len(workload_admins))))
        except Exception as e:
            log.logger.debug('Error occured trying to get all the usernames. Error: {0}'.format(str(e)))

    @staticmethod
    def check_if_enm_accessible():
        """
        Warns the user if password-less access to ENM deployment is not setup
        """
        try:
            log.logger.debug('Establishing if workload has access to ENM deployment')
            enm_access_tuple = check_enm_access()
            if isinstance(enm_access_tuple, tuple):
                enm_access, log_info = enm_access_tuple
                if enm_access:
                    log.logger.debug(log_info)
                else:
                    log.logger.warn(log_info)
        except Exception as e:
            log.logger.debug('Error occured while chekcking password-less access to enm. Error: {0}'.format(e))

    def get_dependent_services_status(self):
        """
        Check the status of the dependent services
        """
        base_message = "\nDependent Services Information"
        tq = ThreadQueue(DEPENDENT_SERVICES, len(DEPENDENT_SERVICES), func_ref=self.check_service_status,
                         args=[SERVICES_NOT_RUNNING])
        tq.execute()
        if SERVICES_NOT_RUNNING:
            log.logger.info(log.green_text(log.underline_text(base_message)))
            log.logger.info(tabulate(SERVICES_NOT_RUNNING, headers=["Service Name", "Service Status"]))

    @staticmethod
    def check_service_status(service, not_running):
        """
        Check status of service and store in the provided list
        :param service: name of the service
        :type service: str

        :param not_running: list where the status NOK needs to be appended
        :type not_running: list
        """
        cmd = '/sbin/service {0} status'.format(service)
        output = commands.getstatusoutput(cmd)
        if output[0]:
            not_running.append((service, log.red_text("NOK")))
        log.logger.debug("Command: {0} executed. Output: {1}".format(cmd, output))

    @staticmethod
    def is_password_ageing_enabled():
        """
        Checks if the ENM Password Ageing Policy is currently enabled using deploymentinfomanager service
        """
        try:
            log.logger.debug('Establishing if ENM Password Ageing Policy is enabled')
            pass_ageing_message = check_password_ageing_policy_status()
            if pass_ageing_message:
                log.logger.warn(pass_ageing_message)
        except Exception as e:
            log.logger.debug('Error occurred while checking ENM Password Ageing Policy. Error: {0}'.format(e))
            if hasattr(e, "message") and " - disable password ageing" in e.message:
                log.logger.warn(e.message)

    def add_output_of_errors_or_warnings(self, profile, issues):
        """
        Adds the error or warning for the supplied profile, max number of errors stored on object is based on the
        "total_number_to_keep" in: profile.add_error_as_string

        :param profile: Profile object to add the errors or warning to
        :type profile: `lib.profile.Profile`
        :param issues: List of either profile errors or profile warnings
        :type issues: list
        """
        for issue in issues[-self.total:]:
            if "DUPLICATES" in issue:
                self.errors_info[profile.NAME].append([issue["TIMESTAMP"], issue["REASON"], issue["DUPLICATES"]])
            else:
                self.errors_info[profile.NAME].append([issue["TIMESTAMP"], issue["REASON"]])

    def _update_status_counts(self, profile, profile_status):
        """
        Increments the various status counters based on the status of the profile

        :param profile_status: The status of the profile
        :type profile_status: str
        :param profile: The `profile.Profile` object
        :type profile: `profile.Profile`
        """

        # It has to be log.yellow_text as otherwise WARNING would not be count as WARNING as there is function that
        # puts status of the profile to green text and I want WARNING to be yellow so it can be more distinguishable
        if profile_status in ['ERROR', 'DEAD', 'WARNING']:
            if profile_status == 'DEAD':
                self.num_dead_profiles += 1
            elif profile_status == 'WARNING':
                self.num_warning_profiles += 1
            else:
                self.num_errored_profiles += 1

        # Don't duplicate DEAD / ERROR / WARNING profiles as totals will not match
        if profile_status not in ['DEAD', 'ERROR', 'WARNING']:
            if profile.state in ['STARTING']:
                self.num_starting_profiles += 1
            if profile.state in ['COMPLETED']:
                self.num_completed_profiles += 1
            if profile.state in ['RUNNING', 'SLEEPING']:
                self.num_running_profiles += 1

    def _sort_profiles(self):
        """
         Sorts the profiles by name or by runtime if the 'sort_by_runtime' was specified
        """

        if self.sort_by_runtime:
            self.profiles_to_print = sorted(self.profiles_to_print, key=lambda profile: profile.get_last_run_time(),
                                            reverse=True)
        else:
            self.profiles_to_print = sorted(self.profiles_to_print, key=lambda profile: profile.NAME)

    def _print_profile_info(self):
        """
        Prints the tabulated summary information about the profiles
        """

        log.logger.info(log.yellow_text("\nLog Files: /var/log/enmutils/daemon/<ProfileName>.log\n"))
        log.logger.info(log.green_text(log.underline_text("Workload Info")))
        log.logger.info(tabulate(
            sorted(self.profiles_info_table_values),
            headers=['Name', 'State', 'Status', 'Started', 'pid', 'Nodes', 'Users', 'Sessions', 'Priority',
                     'Schedule']))
        log.logger.info('\nNote: The "Nodes" column indicates the number of nodes currently reserved by the profile in'
                        ' the workload pool.')

    def _print_error_info(self):
        """
        Prints the profiles error information
        """

        # Print the header
        msg = "Workload Errors and Warnings\n" if self.verbose else "Workload Warnings\n"
        log.logger.info(log.green_text(log.underline_text("Workload Errors" if self.errors_only else msg)))

        log.logger.info(
            log.cyan_text("\nNew error and warning stacking introduced: Duplicate errors and warnings now appear"
                          " as timestamps. The timestamps can be used to search the profile log file."))
        if self.warnings:
            log.logger.info(log.blue_text("\nDue to the need to support backwards compatibility, some corrections to "
                                          "the naming of NetworkElements, may temporarily generate a warning.\nFor "
                                          "more information: https://jira-oss.seli.wh.rnd.internal.ericsson.com/browse/NSS-20643."))

        text_wrapper = TextWrapper(initial_indent='  ', subsequent_indent='  ', width=200,
                                   replace_whitespace=False)
        for name, errors in sorted(self.errors_info.items()):
            self.print_log_file_path(name)
            for error in reversed(errors[-self.total:]):
                error_time = datetime.datetime.strptime(error[0], "%Y/%m/%d %H:%M:%S").strftime("%d-%b %H:%M:%S")
                error_lines = error[1].splitlines()
                log.logger.info('\n'.join(text_wrapper.wrap(
                    "%s: %s: %s" % (log.green_text(name), log.blue_text(error_time), error_lines[0]))))
                for line in error_lines[1:]:
                    log.logger.info('\n'.join(text_wrapper.wrap(line)))
                self.print_duplicate_errors(error, text_wrapper)

    @staticmethod
    def print_log_file_path(profile_name):
        """
        Prints the log file path for the given profile

        :param profile_name: Name of profile
        :type profile_name: str
        """
        log.logger.info("\n" + log.green_text(profile_name) + log.purple_text(" [ Logs : /var/log/enmutils/daemon/" +
                                                                              profile_name.lower() + ".log ]"))
        if "CMIMPORT_" in profile_name:
            log.logger.info(log.green_text(profile_name) + log.cyan_text("[Profile flow diagram: {0}]"
                                                                         .format(IMPORT_URL)))
        elif profile_name == "APT_01":
            log.logger.info("[Further information: {0}]".format(APT_URL))

    @staticmethod
    def print_duplicate_errors(error, text_wrapper):
        """
        Prints duplicate errors if they exist.

        :param error: List containing error parameters.
        :type error: list
        :param text_wrapper: Used to wrap content for printing.
        :type text_wrapper: TextWrapper
        """

        duplicates = error[2] if len(error) > 2 else []
        num_duplicates = len(duplicates)
        if num_duplicates > 0:
            duplicates = [datetime.datetime.strptime(x, "%Y/%m/%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
                          for x in duplicates]
            log.logger.info(
                "".join(text_wrapper.wrap("Number of duplicates : {0} : {1} ".format(num_duplicates, duplicates))))

    def _get_errors_by_type(self, errors):
        """
        Returns errors by user specified type
        :param errors: list of errors.
        :type errors: list
        :return: list of errors by specified type.
        :rtype: list
        """
        wanted_errors = []
        for err_type in self.error_types:
            for error in errors:
                if err_type.upper() in error["REASON"].split(']')[0].upper():
                    wanted_errors.append(error)

        return wanted_errors

    def _print_profile_summary(self):
        """
        Print the table summary of the profile status.
        """

        log.logger.info("{0}".format(log.green_text(log.underline_text("\nProfiles Summary"))))
        log.logger.info(tabulate(
            [[len(self.profiles_to_print), self.num_starting_profiles, self.num_running_profiles,
              self.num_completed_profiles,
              self.num_warning_profiles, self.num_errored_profiles, self.num_dead_profiles, self.sessions["logged_in"],
              self.sessions["total"]]],
            headers=['Total', 'Starting', 'Running',
                     'Completed', "Warning", log.red_text('Errored'), log.red_text('Dead'),
                     'Users Logged In', 'User Sessions'], tablefmt="grid"))

    def _set_profile_sessions(self, profiles):
        """
        Sets number of sessions per profile in a dictionary, logs top 10 session hoarders

        :param profiles: list of profile objects
        :type profiles: list
        """
        log.logger.debug("Setting number of sessions per profile and logging top 10 session hoarders")
        profile_sessions, session_hoarders = get_profile_sessions_info(profiles)
        log.logger.debug("Top 10 Session hoarders: {0}".format(session_hoarders))
        self.sessions = profile_sessions


class ExportProfileOperation(WorkloadOperation):
    TIMESTAMP = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    EXPORT_PROP_FILE_NAME = "_prop_" + TIMESTAMP + ".py"

    def __init__(self, argument_dict, profile_names=None):
        """
        Exports all UPPERCASE profile class properties

        :param profile_names: Specific profiles to export. Defaults to 'None' which exports all profiles.
        :type profile_names: list
        :param argument_dict: dict of arguments with user input
        :type argument_dict: dict
        """
        super(ExportProfileOperation, self).__init__(profile_names)
        self.profile_names = [profile_name.upper() for profile_name in profile_names] if profile_names else []
        self.profiles_to_export = {}
        self.categories_to_export = {}
        self.all_profiles = True if argument_dict['PROFILES'] == 'all' and not argument_dict['--category'] else False
        self.all_categories = True if argument_dict['--category'] and argument_dict['PROFILES'] == 'all' else False
        self.categories = [category.upper() for category in argument_dict['PROFILES'].split(",")] if argument_dict[
            '--category'] else None
        self.export_prop_file_path = config.get_prop('log_dir')

    def _validate(self):
        if self.profile_names:
            for profile in self.profile_names:
                if profile in self.active_profiles:
                    self.profiles_to_export[profile] = self.active_profiles[profile]
        else:
            self.profiles_to_export = self.active_profiles
        if not self.profiles_to_export:
            raise RuntimeError("No profiles found to export.")
        if self.categories:
            for category in self.categories:
                profile_list = []
                for profile_name, profile in self.profiles_to_export.iteritems():
                    if profile_name.split('_')[0] == category or re.split(r'_\d{1,2}', profile_name)[0] == category:
                        profile_list.append(profile)
                if profile_list:
                    self.categories_to_export[category] = profile_list

    def _execute_operation(self):
        """
        Exports profile class properties in to a file in the format profile_name_prop_timestamp.py or
        category_prop_timestamp.py in the present working directory
        """
        if not profilemanager_adaptor.can_service_be_used():
            profilemanager.generate_export_file(profiles_to_export=self.profiles_to_export,
                                                all_profiles=self.all_profiles, all_categories=self.all_categories,
                                                categories_to_export=self.categories_to_export,
                                                export_file_path=self.export_prop_file_path)
        else:
            categories_to_export = {key: [profile.NAME for profile in value] for key, value in
                                    self.categories_to_export.items()}
            profilemanager_adaptor.export_profiles(self.profiles_to_export.keys(), self.export_prop_file_path,
                                                   categories_to_export=categories_to_export,
                                                   all_profiles=self.all_profiles,
                                                   all_categories=self.all_categories)


class RestartProfilesOperation(WorkloadOperation):
    def __init__(self, argument_dict, profile_names=None, ignored_profiles=None):
        """
        Restarts the specified profiles

        :param profile_names: The list of profiles to restart
        :type profile_names: list
        :param ignored_profiles: set, list of profile names to be ignored when restarting
        :type ignored_profiles: list
        :param argument_dict: dict of arguments with user input
        :type argument_dict: dict
        """

        super(RestartProfilesOperation, self).__init__()
        self.argument_dict = argument_dict

        self.profile_names = [profile.upper() for profile in profile_names] if profile_names else []
        self.ignored_profiles = ignored_profiles
        self.force_stop = argument_dict['--force-stop'] if argument_dict['--force-stop'] else False
        self.all_supported_workload = argument_dict['--supported'] if argument_dict['--supported'] else False
        self.updated = argument_dict['--updated'] if argument_dict['--updated'] else False
        self.jenkins = argument_dict['--jenkins'] if argument_dict['--jenkins'] else False

    def _validate(self):
        """
        Validates if profile names or ALL supplied, retrieves the profile names if ALL
        """
        if self.profile_names:
            inactive_profiles = list(set(self.profile_names).difference(set(self.active_profiles.keys())))
            if inactive_profiles:
                log.logger.info(log.yellow_text("The following inactive profile(s) won't start - {0}".
                                                format(inactive_profiles)))
            if not self.active_profiles:
                raise RuntimeError("No profiles to restart.")
            self.profile_names = self.active_profiles.keys()

        else:  # restart all called.
            self.profile_names = load_mgr.get_active_profile_names()

    def _execute_operation(self):
        """
        Restarts the specified profiles
        """
        if self.updated:
            self._restart_updated()

        elif self.all_supported_workload:
            self._execute_restart(all_supported=True)

        else:
            self._execute_restart()

    def _execute_restart(self, all_supported=False):
        """
        Executes Restart of the profile

        :param all_supported: Flag to indicate if all supported profiles shoul dbe restarted
        :type all_supported: bool
        """
        log.logger.debug("Executing profile(s) restart")

        stop = StopOperation(self.argument_dict, self.profile_names, self.ignored_profiles)
        stop.execute()

        load_mgr.wait_for_stopping_profiles(stop.valid_profiles, force_stop=self.force_stop, jenkins=self.jenkins)

        if all_supported:
            self.profile_names = self.supported_profiles

        if "--release-exclusive-nodes" in self.argument_dict and self.argument_dict["--release-exclusive-nodes"]:
            self.argument_dict['--release-exclusive-nodes'] = False

        start = StartOperation(self.argument_dict, self.profile_names, self.ignored_profiles, restart=True)
        start.execute()

        log.logger.debug("Executing profile(s) restart complete")

    def _restart_updated(self):

        self.profile_names = [profile.NAME for profile in load_mgr.get_updated_active_profiles()]

        if self.profile_names:
            self._execute_restart()
        else:
            log.logger.info(log.yellow_text("No profiles found to update."))


class KillOperation(WorkloadInfoOperation):

    def __init__(self, profile_names=None):
        """
               Kills profile when it stucks in start/stop state
               :param profile_names: The list of profiles to kill
               :type profile_names: list
               """
        super(KillOperation, self).__init__(profile_names=profile_names)

    def _validate(self):
        raise NotImplementedError("This method should be overridden by the derived class")

    def _execute_operation(self):
        """
        Executes killOperaation of the profile
        """
        log.logger.info(log.green_text("Note : This command is only for internal use , BR will not own any issues faced if this command is used"))
        log.logger.debug("Kill operation started")
        log.logger.info("Kill operation started")
        log.logger.debug("Fetching all_keys from persistence")
        log.logger.info("Removing profile data keys in persistence")

        all_keys = persistence.get_all_keys()

        log.logger.debug("Found a total of {0} keys from persistence".format(len(all_keys)))

        for profile_name in self.profile_names:

            log.logger.debug("Profile in progress - {0}".format(profile_name))
            profile_keys = [key for key in all_keys if profile_name in key]
            log.logger.debug("Keys to be removed - {0}".format(profile_keys))
            log.logger.info("Keys to be removed - {0}".format(profile_keys))
            for key in all_keys:
                if profile_name in key:
                    log.logger.debug("Keys to be removed - {0}".format(key))
                    persistence.remove(key)

            log.logger.debug("Fetching active workload profiles")

            active_workload_profiles = persistence.get("active_workload_profiles")

            log.logger.debug("{0} exists in active workload profiles list - {1}".
                             format(profile_name, profile_name in active_workload_profiles))
            if profile_name in active_workload_profiles:
                active_workload_profiles.remove(profile_name)
                persistence.set("active_workload_profiles", active_workload_profiles, -1)
                log.logger.debug("{0} was removed in active_workload_profiles list in persistence".format(profile_name in active_workload_profiles))
                log.logger.info("Successfully removed profile {0} data keys in persistence".format(profile_name))
                log.logger.debug("Fetching process id for {0}".format(profile_name))
                log.logger.info("{0} was removed in active_workload_profiles list in persistence.".format(profile_name))
            profile_pid = process.get_profile_daemon_pid(profile_name)
            if profile_pid:
                profile_pid = profile_pid[0]
                log.logger.debug("Process id for {0} - {1}".format(profile_name, profile_pid))
                log.logger.info("Process id for {0} - {1}".format(profile_name, profile_pid))
                process.kill_process_id(int(profile_pid), signal.SIGKILL)
            else:
                log.logger.info("Process id not available for {0}".format(profile_name))
        if not profilemanager_adaptor.can_service_be_used():
            profilemanager.delete_pid_files(self.profile_names)
            log.logger.debug("Deleting all pid files for the following profiles - {0}".format(self.profile_names))
        else:
            profilemanager_adaptor.clear_profile_pid_files(self.profile_names)
            log.logger.debug("successfully killed {0} process id for {1} and pid file".format(profile_pid, self.profile_names))
        log.logger.info(log.green_text("Kill operations completed for {0}".format(self.profile_names)))


class StopOperation(WorkloadOperation):

    def __init__(self, argument_dict, profile_names=None, ignored_profiles=None):
        """
        Stops profiles

        :param argument_dict: dict of arguments with user input
        :type argument_dict: dict
        :param profile_names: A list of specific profile names to stop. If none specified all running profiles are stopped
        :type profile_names: list
        :param ignored_profiles: A list of profile names to ignore when stopping
        :type ignored_profiles: list

        """
        super(StopOperation, self).__init__()

        self.profile_names = [profile.upper() for profile in profile_names] if profile_names else []
        self.ignored_profiles = [profile.upper() for profile in ignored_profiles] if ignored_profiles else []
        self.schedule_file = argument_dict["--schedule"] if argument_dict["--schedule"] else None
        self.force_stop = argument_dict['--force-stop'] if argument_dict['--force-stop'] else False
        self.initial_install_teardown = argument_dict['--initial-install-teardown'] if argument_dict[
            '--initial-install-teardown'] else False
        self.release_nodes = argument_dict['--release-exclusive-nodes'] if argument_dict[
            '--release-exclusive-nodes'] else False
        self.valid_profiles = {}
        self.priority = argument_dict["--priority"]
        self.stop_all = True if argument_dict["PROFILES"] == "all" else False

    def _validate(self):
        """
        Validates profiles to be stopped.
        """
        valid_profiles, profiles_not_started, killed_profiles = [], [], []

        if self.release_nodes and 'EXCLUSIVE-ALLOCATED' in persistence.get_all_keys():
            persistence.remove('EXCLUSIVE-ALLOCATED')

        if self.priority:
            if not self.profile_names:
                self.profile_names = [profile_name.upper() for profile_name in self.active_profiles]
            self.profile_names = load_mgr.get_profiles_with_priority(self.priority, self.profile_names)

        if self.profile_names:
            profiles_to_check = [profile for profile in self.profile_names if profile not in self.ignored_profiles]
            valid_profiles, profiles_not_started, killed_profiles = self._workload_stop_checks(profiles_to_check)
            self.profile_names = valid_profiles
            self._set_active_profiles(specific_profiles=valid_profiles)
            self.valid_profiles = {profile: profile_obj for profile, profile_obj in self.active_profiles.iteritems()
                                   if profile not in self.ignored_profiles and profile in valid_profiles}
        else:
            self.valid_profiles = {profile: profile_obj for profile, profile_obj in self.active_profiles.iteritems()
                                   if profile not in self.ignored_profiles}

        if not self.force_stop:
            self._remove_foundation_profiles()

        if profiles_not_started:
            log.logger.info("The following profiles were not started: [{0}]".format(", ".join(profiles_not_started)))
        if killed_profiles:
            log.logger.warn("The following profiles were killed due to profile missing from persistence: [{0}]. "
                            "For more information see debug logs and profile daemon logs.\n"
                            "Logs directory: {1}".format(", ".join(killed_profiles), config.get_log_dir()))
        if not self.valid_profiles and not self.release_nodes:
            raise RuntimeError("No profiles to stop.")

    def _execute_operation(self):
        """
        Stops profiles
        """
        if self.initial_install_teardown:
            self._initial_install_teardown()
        else:
            if self.release_nodes:
                load_mgr.deallocate_all_exclusive_nodes(self.profile_names, stop_all=self.stop_all,
                                                        service_to_be_used=self.nodemanager_service_to_be_used)
            if self.valid_profiles:
                self.schedule_stop_by_group()

    def schedule_stop_by_group(self):
        """
        Group profile(s) by category and create scheduler object per group, before calling stop function
        """
        groups = self.group_profiles_by_category()
        schedule_objects = []
        for profiles in groups.values():
            schedule = workload_schedule.WorkloadSchedule(schedule_file=self.schedule_file,
                                                          profile_dict=profiles,
                                                          initial_install_teardown=self.initial_install_teardown,
                                                          release_nodes=self.release_nodes)
            schedule_objects.append(schedule)
        tq = ThreadQueue(schedule_objects, num_workers=len(schedule_objects),
                         func_ref=self.stop_func, task_wait_timeout=STOP_CMD_THREAD_TIMEOUT)
        tq.execute()
        log.logger.info("Workload {0} initiation completed. Issue command 'workload"
                        " status' to see the status of the profiles. ".format(log.green_text("stop")))

    @staticmethod
    def stop_func(scheduler):
        """
        Call the stop function on the supplied scheduler object

        :param scheduler: Scheduler object to invoke the stop function
        :type scheduler: `workload_schedule.WorkloadSchedule`
        """
        log.logger.debug("Attempting to stop the following profiles: [{0}].".format(scheduler.profile_dict.keys()))
        scheduler.stop()

    def group_profiles_by_category(self):
        """
        Groups the valid profile dict by category into category dictionaries
        """
        profile_groups = {}
        for profile_name, profile_obj in self.valid_profiles.items():
            category = re.split(r'_\d+', profile_name.upper())[0].split('_SETUP')[0]
            if category not in profile_groups.keys():
                profile_groups[category] = {}
            profile_groups[category][profile_name] = profile_obj
        return profile_groups

    def _remove_foundation_profiles(self):
        """
        Removes foundation level profiles if --force-stop is not supplied
        """
        active_foundation_profiles = load_mgr.get_active_foundation_profiles()
        foundation_profiles_not_stopping = []
        for profile in self.valid_profiles.keys():
            if profile in active_foundation_profiles:
                foundation_profiles_not_stopping.append(profile)
                self.valid_profiles.pop(profile)
        if foundation_profiles_not_stopping:
            log.logger.info(log.yellow_text("The following profiles are FOUNDATION profiles "
                                            "and will need to be stopped with --force-stop option. "
                                            "[{0}]".format(",".join(foundation_profiles_not_stopping))))

    @staticmethod
    def _initial_install_teardown():
        """
        Option to simply kill every profile daemon and clear persistence, and the existing enmutil directories
        """
        log.logger.info("\nForcefully killing any workload daemon processes still running.")
        common_utils.ensure_all_daemons_are_killed()
        dirs = ["/var/tmp/enmutils /var/log/enmutils/daemon /home/enmutils/dynamic_content"]
        log.logger.info("Clearing ENMUtil directories: [{0}].".format(" ".join(dirs)))
        shell.run_local_cmd(shell.Command("rm -rf {0}".format(" ".join(dirs))))
        log.logger.info("Clearing persistence values.")
        shell.run_local_cmd(shell.Command("/opt/ericsson/enmutils/bin/persistence clear force --auto-confirm"))
        nodemanager_adaptor.update_nodes_cache_on_request()

    def _workload_stop_checks(self, profile_names):
        """
        Carries out checks on profiles to prepare for WorkloadStopOperation.
        :param profile_names: Profile name to retrieve from persistence
        :type profile_names: list
        :return: tuple of lists containing valid profiles, profiles not started and profiles that have been killed.
        :rtype: tuple
        """
        profile_not_started = []
        profiles_killed = []
        valid_profiles = []
        profile_state_lists = tuple([valid_profiles, profile_not_started, profiles_killed])
        for profile_name in profile_names:
            profile_persisted = persistence.has_key(profile_name)
            in_active_list = profile_name in load_mgr.get_active_profile_names()
            profile_process_running = True if process.get_profile_daemon_pid(profile_name) else False

            self._determine_stopping_action(profile_name, profile_state_lists, profile_persisted, in_active_list,
                                            profile_process_running)

        return profile_state_lists

    @staticmethod
    def _determine_stopping_action(profile_name, profile_state_lists, profile_persisted, in_active_list,
                                   profile_process_running):
        """
        Analyses profile state and prepares the profile for stopping.
        Profile will be killed if no persisted profile object.
        The profiles_states_lists tuple is updated depending on the current state of the profile.
        :param profile_name: Profile name to check.
        :type profile_name: str
        :param profile_state_lists: Tuple containing lists of profiles depending on their running state.
                                    Order of lists => (valid_profiles, profile_not_started, profiles_killed)
        :type profile_state_lists: tuple
        :param profile_persisted: Is the profile object in persistence.
        :type profile_persisted: bool
        :param in_active_list: Is the profile in active_workload_profiles.
        :type in_active_list: bool
        :param profile_process_running: Boolean to indicate if process is running
        :type profile_process_running: bool
        """
        log.logger.debug('Current {0} state: persisted:{1}, in_active_workload_profiles:{2}, process running:{3}'
                         .format(profile_name, profile_persisted, in_active_list, profile_process_running))

        if profile_persisted and in_active_list:
            profile_state_lists[0].append(profile_name)
        elif not profile_persisted and not in_active_list and not profile_process_running:
            profile_state_lists[1].append(profile_name)
        elif not profile_persisted and in_active_list:
            log.logger.debug('Profile object is not in persistence but contained in active_workload_profiles. '
                             'Profile will be removed from active profile list.')
            remove_profile_from_active_workload_profiles(profile_name)
            if profile_process_running:
                log.logger.debug('Active process running for profile. Attempting to stop.')
                load_mgr.kill_profile_daemon_process(profile_name)
                profile_state_lists[2].append(profile_name)
            else:
                profile_state_lists[1].append(profile_name)

        elif not profile_persisted and profile_process_running:
            log.logger.debug("Profile is not persisted but has a process running. Process will be killed")
            load_mgr.kill_profile_daemon_process(profile_name)
            profile_state_lists[2].append(profile_name)
        else:
            log.logger.debug('Profile is persisted but missing from active_workload_profiles. '
                             'Profile will be added to active profiles list')
            add_profile_to_active_workload_profiles(profile_name)
            profile_state_lists[0].append(profile_name)
        log.logger.debug("Determine stopping action - complete")


class StartOperation(WorkloadHealthCheckOperation):
    def __init__(self, argument_dict, profile_names=None, ignored_profiles=None, restart=None):

        """
        Start profiles

        :param argument_dict: dict of arguments with user input
        :type argument_dict: dict
        :param profile_names: A list of profile names to start. 'None' will start all profiles
        :type profile_names: list
        :param ignored_profiles: The profiles to ignore while starting nodes from a particular category
        :type ignored_profiles: list
        :param restart: Flag controlling restart
        :type restart: bool
        """

        super(StartOperation, self).__init__(health_check=argument_dict['--network-check'],
                                             no_exclusive=argument_dict['--no-exclusive'], restart=restart,
                                             no_network_size_check=argument_dict['--no-network-size-check'])
        self.argument_dict = argument_dict
        self.profile_names = [profile_name.upper() for profile_name in profile_names] if profile_names else []
        self.dependent_profiles = []
        self.ignored_profiles = [profile.upper() for profile in ignored_profiles] if ignored_profiles else []
        self.schedule_file = argument_dict["--schedule"] if argument_dict["--schedule"] else None
        self.config_file = argument_dict["--conf"] if argument_dict["--conf"] else None
        if self.config_file:
            config.set_prop('config-file', self.config_file)
        self.force = argument_dict['--force'] if argument_dict['--force'] else False
        additional_supported_types = argument_dict['--include'].split(',') if argument_dict['--include'] else []
        additional_supported_types.append(True)
        cache.set("valid_supported_types", additional_supported_types)
        self.release_nodes = argument_dict['--release-exclusive-nodes']
        self.valid_profiles = {}
        self.priority = argument_dict['--priority']
        self.new_only = argument_dict['--new-only'] if argument_dict['--new-only'] else False
        self.updated = argument_dict['--updated'] if argument_dict['--updated'] else False
        self.operation_type = "start"

    def _validate(self):
        """
        Validates profiles to be started.
        """
        if not self.profile_names and self.new_only:
            raise RuntimeError("No profiles to start.")

        if not self.profile_names and self.updated:
            raise RuntimeError("No profiles to start.")

        if self.release_nodes and 'EXCLUSIVE-ALLOCATED' in persistence.get_all_keys():
            persistence.remove('EXCLUSIVE-ALLOCATED')
        unsupported_profiles_called = []
        unsupported_profiles_in_physical_called = []
        unsupported_profiles_in_cloud_called = []
        unsupported_profiles_in_cloud_native_called = []
        if not self.profile_names:
            self.profile_names = [profile_name.upper() for profile_name in self.supported_profiles]

        if self.priority:
            self.profile_names = list(load_mgr.get_profiles_with_priority(self.priority, self.profile_names))

        self._remove_already_started_profiles()

        (unsupported_profiles_in_physical_called, unsupported_profiles_in_cloud_called,
         unsupported_profiles_in_cloud_native_called,
         unsupported_profiles_called) = self._get_profile_objects_and_categorize(unsupported_profiles_in_cloud_called,
                                                                                 unsupported_profiles_in_cloud_native_called,
                                                                                 unsupported_profiles_called,
                                                                                 unsupported_profiles_in_physical_called)
        if unsupported_profiles_called:
            log.logger.info(log.yellow_text("Skipping unsupported profile(s). "
                                            "The following profiles were not started: "
                                            "[{0}]".format(",".join(unsupported_profiles_called[:10]))))
        if unsupported_profiles_in_physical_called:
            log.logger.info(log.yellow_text("Skipping unsupported profile(s) in physical deployment. "
                                            "The following profiles were not started: "
                                            "[{0}]".format(",".join(unsupported_profiles_in_physical_called[:10]))))
        if unsupported_profiles_in_cloud_called:
            log.logger.info(log.yellow_text("Skipping unsupported profile(s) in openstack cloud deployment. "
                                            "The following profiles were not started: "
                                            "[{0}]".format(",".join(unsupported_profiles_in_cloud_called[:10]))))
        if unsupported_profiles_in_cloud_native_called:
            log.logger.info(log.yellow_text("Skipping unsupported profile(s) in cloud native deployment. "
                                            "The following profiles were not started: "
                                            "[{0}]".format(",".join(unsupported_profiles_in_cloud_native_called[:10]))))

        self.dependent_profiles = [profile_name for profile_name in
                                   load_mgr.get_dependent_profiles(self.valid_profiles.keys())
                                   if profile_name not in self.valid_profiles.keys() and
                                   profile_name in load_mgr.get_active_profile_names()]

        log.logger.debug("Valid profiles to start : {}, dependent profiles(active) to restart : {}"
                         .format(self.valid_profiles.keys(), self.dependent_profiles))
        if not self.valid_profiles:
            raise RuntimeError("No profiles to start.")

    def _get_profile_objects_and_categorize(self, unsupported_profiles_in_cloud_called,
                                            unsupported_profiles_in_cloud_native_called,
                                            unsupported_profiles_called, unsupported_profiles_in_physical_called):
        """
        Get profile objects and categorize them based on whether they are supported
        in physical, cloud or cloud native deployments.

        :param unsupported_profiles_in_cloud_called: list of unsupported profiles in cloud to be updated
        :type unsupported_profiles_in_cloud_called: list
        :param unsupported_profiles_in_cloud_native_called: list of unsupported profiles in cloud native to be updated
        :type unsupported_profiles_in_cloud_native_called: list
        :param unsupported_profiles_called: list of unsupported profiles to be updated
        :type unsupported_profiles_called: list
        :param unsupported_profiles_in_physical_called: list of unsupported profiles in physical to be updated
        :type unsupported_profiles_in_physical_called: list
        :return: tuple of lists of values categorized as unsupported in
                 openstack cloud, cloud native and physical deployments
        :rtype: tuple
        """
        if self.profile_names:
            profile_objects = profile_properties_manager.ProfilePropertiesManager(self.profile_names,
                                                                                  self.config_file).get_profile_objects()
            valid_supported_types = cache.get('valid_supported_types') if cache.has_key('valid_supported_types') else [
                True]
            if not self.force:
                (unsupported_profiles_in_physical_called, unsupported_profiles_in_cloud_called,
                 unsupported_profiles_in_cloud_native_called,
                 unsupported_profiles_called) = self._categorize_profiles(profile_objects, valid_supported_types,
                                                                          unsupported_profiles_in_cloud_called,
                                                                          unsupported_profiles_in_cloud_native_called,
                                                                          unsupported_profiles_called,
                                                                          unsupported_profiles_in_physical_called)
            else:
                self.valid_profiles = {profile_object.NAME: profile_object for profile_object in
                                       profile_objects if profile_object.NAME not in self.ignored_profiles}
        return (unsupported_profiles_in_physical_called, unsupported_profiles_in_cloud_called,
                unsupported_profiles_in_cloud_native_called, unsupported_profiles_called)

    def _categorize_profiles(self, profile_objects, valid_supported_types,
                             unsupported_profiles_in_cloud_called,
                             unsupported_profiles_in_cloud_native_called,
                             unsupported_profiles_called, unsupported_profiles_in_physical_called):
        """
        Categorize profiles whether they are unsupported in physical, cloud or cloud native
        deployments.

        :param profile_objects: list of profile objects to be categorized
        :type profile_objects: list
        :param valid_supported_types:
        :type valid_supported_types: list
        :param unsupported_profiles_in_cloud_called: list of unsupported profiles in cloud to be updated
        :type unsupported_profiles_in_cloud_called: list
        :param unsupported_profiles_in_cloud_native_called: list of unsupported profiles in cloud native to be updated
        :type unsupported_profiles_in_cloud_native_called: list
        :param unsupported_profiles_called: list of unsupported profiles to be updated
        :type unsupported_profiles_called: list
        :param unsupported_profiles_in_physical_called: list of unsupported profiles in physical to be updated
        :type unsupported_profiles_in_physical_called: list
        :return: tuple of lists of values categorized as unsupported in
                 openstack cloud, cloud native and physical deployments
        :rtype: tuple
        """
        for profile in profile_objects:
            if profile.NAME not in self.ignored_profiles:
                if hasattr(profile, "SUPPORTED") and profile.SUPPORTED in valid_supported_types:
                    (unsupported_profiles_in_physical_called, unsupported_profiles_in_cloud_called,
                     unsupported_profiles_in_cloud_native_called) = self._categorize_profile(profile,
                                                                                             unsupported_profiles_in_cloud_called,
                                                                                             unsupported_profiles_in_cloud_native_called,
                                                                                             unsupported_profiles_in_physical_called)
                else:
                    unsupported_profiles_called.append(profile.NAME)
        return (unsupported_profiles_in_physical_called, unsupported_profiles_in_cloud_called,
                unsupported_profiles_in_cloud_native_called, unsupported_profiles_called)

    def _categorize_profile(self, profile,
                            unsupported_profiles_in_cloud_called,
                            unsupported_profiles_in_cloud_native_called, unsupported_profiles_in_physical_called):
        """
        Categorize a profile whether it is unsupported in cloud or cloud native deployments.

        :param profile: profile object to be categorized
        :type profile: `enmutils_int.lib.profile.Profile`
        :param unsupported_profiles_in_cloud_called: list of unsupported profiles in cloud to be updated
        :type unsupported_profiles_in_cloud_called: list
        :param unsupported_profiles_in_cloud_native_called: list of unsupported profiles in cloud native to be updated
        :type unsupported_profiles_in_cloud_native_called: list
        :param unsupported_profiles_in_physical_called: list of unsupported profiles in physical to be updated
        :type unsupported_profiles_in_physical_called: list
        :return: tuple of lists of values to be categorized as unsupported in physical,
                 openstack cloud and cloud native deployments
        :rtype: tuple
        """
        if is_host_physical_deployment() and hasattr(profile, "PHYSICAL_SUPPORTED") and not profile.PHYSICAL_SUPPORTED:
            unsupported_profiles_in_physical_called.append(profile.NAME)
        elif cache.is_emp() and hasattr(profile, "CLOUD_SUPPORTED") and not profile.CLOUD_SUPPORTED:
            unsupported_profiles_in_cloud_called.append(profile.NAME)
        elif is_enm_on_cloud_native() and not profile.CLOUD_NATIVE_SUPPORTED:
            unsupported_profiles_in_cloud_native_called.append(profile.NAME)
        else:
            self.valid_profiles[profile.NAME] = profile

        return (unsupported_profiles_in_physical_called, unsupported_profiles_in_cloud_called,
                unsupported_profiles_in_cloud_native_called)

    def _execute_operation(self):
        """
        Starts profiles
        """
        deployment_info_helper_methods.output_network_basic()
        if not self.no_exclusive:
            self._allocate_nodes_to_exclusive_profiles()
        schedule = workload_schedule.WorkloadSchedule(schedule_file=self.schedule_file,
                                                      profile_dict=self.valid_profiles,
                                                      release_nodes=self.release_nodes)
        schedule.start()
        if self.dependent_profiles:
            log.logger.info(log.green_text("Restarting dependent profile(s): {0}".format(sorted(self.dependent_profiles))))
            restart = RestartProfilesOperation(self.argument_dict, self.dependent_profiles, self.ignored_profiles)
            restart.execute()
        else:
            log.logger.debug("No dependent profiles")

    def _allocate_nodes_to_exclusive_profiles(self):
        """
        Allocate nodes to exclusive profiles
        """
        log.logger.debug("Initialize cached nodes list")

        if self.nodemanager_service_to_be_used:
            node_pool_mgr.cached_nodes_list = nodemanager_adaptor.get_list_of_nodes_from_service(
                node_attributes=["node_id", "profiles"])
            self._allocate_exclusive_nodes(profile_list=self.profile_names, service_to_be_used=True)
        else:
            with node_pool_mgr.mutex():
                node_pool_mgr.cached_nodes_list = node_pool_mgr.get_pool().nodes
                self._allocate_exclusive_nodes(profile_list=self.profile_names, service_to_be_used=False)

    def _remove_already_started_profiles(self):
        """
        Removes profiles from starting list if profile already started.
        """
        already_started_profiles = []
        for profile in self.profile_names[:]:
            process_running = True
            in_active_profiles, profile_obj = self.check_if_profile_active_and_loadable_from_persistence(profile)

            if not process.get_profile_daemon_pid(profile):
                process_running = False
            if process_running or profile_obj or in_active_profiles:
                self.profile_names.remove(profile)
                if profile not in self.ignored_profiles:
                    already_started_profiles.append(profile)
                    if profile_obj and not process_running and profile_obj.state != 'COMPLETED':
                        log.logger.warn('{0} has no process running and is not in completed state. This is an '
                                        'unexpected state.\nRun profile stop/start to return profile to correct state. '
                                        'See debug and profile daemon logs for more information.'.format(profile))

        if already_started_profiles:
            log.logger.info(
                "The following profiles were already started: [{0}]".format(", ".join(already_started_profiles)))

    def check_if_profile_active_and_loadable_from_persistence(self, profile):
        """
        Check if Key can be loaded from persistence successfully, remove from persistence, and active list if not

        :param profile: Name of the profile to verify
        :type profile: str

        :return: Tuple indicating if the profile is in active list, and the profile obj
        :rtype: tuple
        """
        if not persistence.has_key(profile):
            return bool(profile in self.active_profiles), None
        profile_obj = persistence.get(profile)
        if not profile_obj:
            profile_mgr = profile_manager.ProfileManager(profile_obj)
            profile_mgr.remove_corrupted_profile_keys_and_update_active_list(profile_name=profile)
            return False, None
        return profile in self.active_profiles, profile_obj


class DiffOperation(WorkloadInfoOperation):

    def __init__(self, argument_dict, profile_names=None):
        """
        Operation object which executes workload diff.
        :param argument_dict: dict of arguments with user input
        :type argument_dict: dict
        :param profile_names: A list of profile names to start. 'None' will start all profiles
        :type profile_names: list
        """
        super(DiffOperation, self).__init__(profile_names)

        self.version = argument_dict['--rpm-version'] if argument_dict['--rpm-version'] else ""
        self.updated = argument_dict['--updated'] if argument_dict['--updated'] else False
        self.priority = argument_dict['--priority'] if argument_dict['--priority'] else 0
        self.list_format = argument_dict['--list-format'] if argument_dict['--list-format'] else False
        self.no_ansi = argument_dict['--no-ansi']
        self.wl_enm_nodes_diff = argument_dict["--nodes"]
        self.wl_enm_poids_diff = argument_dict["--node-poids"]

    def _validate(self):
        """ Implementing abstract method """

    def _execute_operation(self):
        parameters = {"updated": self.updated, "list_format": self.list_format, "version": self.version,
                      "profile_names": self.profile_names, "priority": self.priority, "no_ansi": self.no_ansi,
                      "wl_enm_nodes_diff": self.wl_enm_nodes_diff, "wl_enm_poids_diff": self.wl_enm_poids_diff}
        if profilemanager_adaptor.can_service_be_used():
            profilemanager_adaptor.diff_profiles(**parameters)
        else:
            profilemanager_helper_methods.diff_profiles(**parameters)


class CleanPID(WorkloadInfoOperation):

    def _validate(self):
        log.logger.debug("Skipping validation for clean pid")

    def execute(self):
        self._execute_operation()

    def _execute_operation(self):
        """
        Executes the tool operation
        """
        if not profilemanager_adaptor.can_service_be_used():
            profilemanager.delete_pid_files(self.profile_names)
        else:
            profilemanager_adaptor.clear_profile_pid_files(self.profile_names)


class ClearErrors(WorkloadInfoOperation):
    def __init__(self, profile_names=None):
        super(ClearErrors, self).__init__()

        self.profile_names = profile_names

    def _validate(self):
        pass

    def _execute_operation(self):
        """
        Execute the tool operation
        """
        if not profilemanager_adaptor.can_service_be_used():
            load_mgr.clear_profile_errors(self.profile_names)
        else:
            profilemanager_adaptor.clear_profile_exceptions(self.profile_names)


def get_workload_operations(operation_type, argument_dict, profile_names=None, ignored_profiles=None):
    """
    Returns the workload operation object.

    :param operation_type: the operation to be executed
    :type operation_type: str
    :param argument_dict: argument dictionary with user input.
    :type argument_dict: dict
    :param profile_names: list of profile names to be used
    :type profile_names: list
    :param ignored_profiles: set, list of profile names to be ignored
    :type ignored_profiles: list

    :return: WorkloadOperation object
    :rtype: workload_ops.WorkloadOperations
    """

    operations_classes = {
        "start": {"operation": StartOperation,
                  "kwargs": {'argument_dict': argument_dict, 'profile_names': profile_names,
                             'ignored_profiles': ignored_profiles}},
        "stop": {"operation": StopOperation, "kwargs": {'argument_dict': argument_dict, 'profile_names': profile_names,
                                                        'ignored_profiles': ignored_profiles}},
        "restart": {"operation": RestartProfilesOperation,
                    "kwargs": {'argument_dict': argument_dict, 'profile_names': profile_names,
                               'ignored_profiles': ignored_profiles}},
        "export": {"operation": ExportProfileOperation,
                   "kwargs": {'argument_dict': argument_dict, 'profile_names': profile_names}},
        "status": {"operation": StatusOperation,
                   "kwargs": {'argument_dict': argument_dict, 'profile_names': profile_names}},
        "list": {"operation": ListNodesOperation, "kwargs": {'argument_dict': argument_dict}},
        "describe": {"operation": WorkloadDescriptionOperation, "kwargs": {'profile_names': profile_names}},
        "category": {"operation": DisplayCategoriesOperation, "kwargs": {}},
        "profiles": {"operation": DisplayProfilesOperation, "kwargs": {'argument_dict': argument_dict}},
        "diff": {"operation": DiffOperation,
                 "kwargs": {'argument_dict': argument_dict, 'profile_names': profile_names}},
        "clean-pid": {"operation": CleanPID, "kwargs": {'profile_names': profile_names}},
        "clear-errors": {"operation": ClearErrors, "kwargs": {'profile_names': profile_names}},

        "kill": {"operation": KillOperation, "kwargs": {'profile_names': profile_names}},
    }

    return operations_classes[operation_type]["operation"](**operations_classes[operation_type]["kwargs"])
