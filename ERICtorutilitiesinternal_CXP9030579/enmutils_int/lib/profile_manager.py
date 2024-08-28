# ********************************************************************
# Name    : Profile Manager
# Summary : Primary responsibility is start and stop of profile objects.
#           Used by the workload tool to manage the start, of a profile
#           daemon, stop of a profile daemon, clean up of hung profiles,
#           prevention of duplicate daemon processes, and some
#           functionality around node allocations.
# ********************************************************************

import signal
import time

from enmutils.lib import cache, config, filesystem, log, multitasking, persistence, shell, mutexer, process
from enmutils.lib.exceptions import EnvironError, NoNodesAvailable, ProfileAlreadyRunning
from enmutils.lib.multitasking import UtilitiesDaemon
from enmutils_int.lib import node_pool_mgr, profile
from enmutils_int.lib.services import nodemanager_adaptor


class WorkloadVMDetected(EnvironError):
    pass


def lock_profile(func):
    """
    Decorator function which persists <ACTION>_<PROFILE>_lock.

    :param func: Function to be locked
    :type func: callable

    :raises ProfileAlreadyRunning: raised if the profile is already running

    :return: Decorator wrapper
    :rtype: object
    """

    def wrapper(obj, *args, **kwargs):
        method_name = func.__name__
        if not persistence.has_key("{0}_{1}_lock".format(method_name, obj.profile.NAME)):
            return_value = func(obj, *args, **kwargs)
            # persist the profile lock
            persistence.set("{0}_{1}_lock".format(method_name, obj.profile.NAME), "", 5)
        else:
            raise ProfileAlreadyRunning("Profile is already starting/stopping ", obj.profile.pid)
        return return_value

    return wrapper


class ProfileManager(object):

    def __init__(self, profile, release_nodes=True):
        """
        ProfileManager constructor

        :param profile: Profile to be managed
        :type profile: `enmutils_int.lib.Profile`
        :param release_nodes:  Boolean flag indicating whether or not to release EXCLUSIVE nodes
        :type release_nodes: bool
        """
        self.profile = profile
        self.release_nodes = release_nodes
        self.cmsync_node_allocations = None
        self.nodemanager_service_can_be_used = False
        self.nodes_mgr = node_pool_mgr

    def _profile_is_stopping(self):
        """
        Returns True if profile is in a stopping state.

        :return: Boolean indicating whether or the profile is already stopping
        :rtype: bool
        """
        if self.profile.state == 'STOPPING' and self.profile.running:
            log.logger.warn('Already stopping the profile: {0}. Wait till it finishes.'.format(self.profile.NAME))
            return True
        return False

    def _retain_or_release_nodes(self):
        """
        Functionality to manage the allocation of nodes to EXCLUSIVE profiles
        """
        if self.release_nodes:
            # If release flag is set, go ahead and try to deallocate and then allocate
            self.nodes_mgr.deallocate_nodes(self.profile)
            self.nodes_mgr.allocate_nodes(self.profile)
        elif not self._exclusive_profile_nodes_allocated():
            # Release nodes is False, but if we are short nodes, attempt to allocate more
            self.nodes_mgr.allocate_nodes(self.profile)
        else:
            # Release no nodes and we already have enough
            total_nodes_allocated = len(self.profile.get_nodes_list_by_attribute())
            self.profile.num_nodes = total_nodes_allocated
            log.logger.info("{0} has started with {1} nodes already allocated. Run workload stop/restart {0} "
                            "--release-exclusive-nodes, to start with new nodes."
                            .format(self.profile.NAME, total_nodes_allocated))

    def _profile_requires_nodes(self):
        """
        Indicates if the profile object has node related attributes

        :return: Indicates if the profile object has node related attributes
        :rtype: bool
        """

        return hasattr(self.profile, "NUM_NODES") or hasattr(self.profile, "SUPPORTED_NODE_TYPES")

    def _allocate_nodes_to_profile(self):
        """
        Allocates nodes to a profile. The profile_lock is persisted so that the same profile
        cannot be allowed to be started twice.
        """
        log.logger.debug("Allocation of nodes to profile (if applicable)")
        if self._profile_requires_nodes():
            if not self.profile.EXCLUSIVE:
                log.logger.debug("Allocation of nodes to non-exclusive profile")
                self.nodes_mgr.allocate_nodes(self.profile)
            else:
                log.logger.debug("Retain or release nodes for exclusive profile")
                self._retain_or_release_nodes()
            log.logger.debug("Allocation of nodes to profile - complete")
        else:
            log.logger.debug("The profile {0} is not dependent on nodes".format(self.profile))

    def _exclusive_profile_nodes_allocated(self):
        """
        Check if the profile already has all of its required nodes allocated

        :return: Boolean indicating if profile has all of its nodes allocated
        :rtype: bool
        """
        if self.nodemanager_service_can_be_used:
            _, _, all_nodes = nodemanager_adaptor.list_nodes(node_attributes=["profiles"])
            allocated_node_count = len([node for node in all_nodes if self.profile.NAME in node.profiles])
            number_of_required_nodes = self._calculate_required_nodes(all_nodes)

        else:
            with node_pool_mgr.mutex():
                pool = node_pool_mgr.get_pool()
                allocated_node_count = len(pool.allocated_nodes(self.profile))
                number_of_required_nodes = self._calculate_required_nodes(pool.nodes)

        return allocated_node_count == number_of_required_nodes

    def _calculate_required_nodes(self, all_nodes):
        """
        Determine if the profile has enough nodes already allocated

        :param all_nodes: List of all node objects
        :type all_nodes: list

        :return: Number of nodes required
        :rtype: int
        """
        if hasattr(self.profile, 'TOTAL_NODES'):
            return self.profile.TOTAL_NODES
        else:
            number_of_nodes_required = 0
            for node_type, node_count in self.profile.NUM_NODES.iteritems():
                number_of_nodes_required += (len([node for node in all_nodes if node.primary_type == node_type])
                                             if node_count == -1
                                             else node_count)
            return number_of_nodes_required

    def remove_from_active_profiles_list(self, profile_name=None):
        """
        Removes the failed to start profile from the active profiles list

        :param profile_name: Name of the profile to be removed from the active list
        :type profile_name: str
        """
        profile_name = getattr(self.profile, "NAME", profile_name)
        with mutexer.mutex("workload_profile_list", persisted=True):
            active_profiles = persistence.get("active_workload_profiles")
            if active_profiles and profile_name in active_profiles:
                active_profiles.remove(profile_name)
                persistence.set("active_workload_profiles", active_profiles, -1)

    def remove_corrupted_profile_keys_and_update_active_list(self, profile_name):
        """
        Remove profile key from persistence, and active list

        :param profile_name: Name of the profile to verify
        :type profile_name: str
        """
        persistence.remove(profile_name)
        self.remove_from_active_profiles_list()

    @lock_profile
    def start(self):
        """
        Allocates nodes and calls _start a profile.

        :raises NoNodesAvailable: raised if no nodes are available for allocation
        :raises ProfileAlreadyRunning: raised if profile is already running
        :raises Exception: raised if start encounters an error
        """
        if nodemanager_adaptor.can_service_be_used(self.profile):
            self.nodemanager_service_can_be_used = True
            self.nodes_mgr = nodemanager_adaptor

        architecture_type = "services" if self.nodemanager_service_can_be_used else "legacy"
        log.logger.debug("Using {0} architecture for node allocation".format(architecture_type))

        try:
            self._allocate_nodes_to_profile()
        except NoNodesAvailable as e:
            log.logger.error(e.message)
            self.profile.clear_errors()
            self.profile.add_error_as_exception(e=e)
            self.profile.run_profile = False
            raise
        finally:
            try:
                self._start()
            except ProfileAlreadyRunning:
                raise
            except Exception:
                if hasattr(self.profile, "NUM_NODES") and self.release_nodes:
                    self.nodes_mgr.deallocate_nodes(self.profile)
                self.remove_from_active_profiles_list()
                raise

    @lock_profile
    def stop(self):
        """
        Calls _stop on a profile if profile is not already stopping.

        :raises ProfileAlreadyRunning: raised if profile is already stopping
        """
        if nodemanager_adaptor.can_service_be_used(self.profile):
            self.nodemanager_service_can_be_used = True
            self.nodes_mgr = nodemanager_adaptor

        log.logger.info(log.green_text('Attempting to stop: {0}'.format(self.profile.NAME)))
        if self._profile_is_stopping():
            raise ProfileAlreadyRunning("Profile already stopping.", self.profile.pid)
        else:
            self._stop()
            self.checks_profile_is_stopping()

    def checks_profile_is_stopping(self):
        """
        Checks the profiles status and kills the process if it is hanging
        """
        count = 0
        while count < 300:
            # Retrieve the latest persisted object which should have the updated state
            updated_profile = persistence.get(self.profile.NAME)
            if not updated_profile or getattr(updated_profile, 'state', None) == 'STOPPING':
                return
            time.sleep(1)
            count += 1
            if count % 60 == 0:
                log.logger.info("{0} stop initiation still in progress.".format(self.profile.NAME))
        log.logger.debug("Profile has failed to respond to Keyboard Interrupt - terminating processes")
        process.kill_pid(self.profile.pid, signal.SIGKILL)
        log.logger.debug("Now attempting to initiate the stop profile daemon")
        self._stop()

    def _start(self):
        """
        Starts a profile.
        """

        daemon = ProfileDaemon(
            self.profile.NAME, self.profile, log_identifier=self.profile.NAME)
        daemon.close_all_fds = True
        daemon.start()
        log.logger.info(log.green_text(
            "Successfully initiated the profile {0}.\nYou may watch/tail the logs to view it's progress located: "
            "{1}/daemon/{2}.log".format(self.profile.NAME.upper(), config.get_log_dir(), self.profile.NAME.lower())))

    def _stop(self):
        """
        Stops a profile
        """
        if self.profile.EXCLUSIVE and self.release_nodes:
            self.nodes_mgr.deallocate_nodes(self.profile)
            log.logger.info(log.cyan_text("Deallocated all nodes from the profile: '{0}'".format(self.profile)))
        if (isinstance(self.profile, profile.CMImportProfile) and
                (not self.profile.EXCLUSIVE or (self.profile.EXCLUSIVE and self.release_nodes))):
            persistence.remove('%s-mos' % self.profile.NAME)
        if self.profile.running:
            log.logger.debug("Profile processes are still running")
            process.kill_spawned_process(self.profile.NAME, self.profile.pid)
            log.logger.debug("Initiating teardown in running profile by sending interrupt (SIGINT) to profile "
                             "process pid {0}".format(self.profile.pid))
            process.kill_process_id(self.profile.pid, signal.SIGINT)
        else:
            log.logger.debug("No profile processes found - initiating teardown daemon for profile")
            multitasking.UtilitiesDaemon(self.profile.NAME + '_stop', self.profile, log_identifier=self.profile.NAME,
                                         args=[True]).start()

        log.logger.info(log.green_text("Successfully initiated the '%s' profile teardown" % self.profile.NAME))
        return True

    def initial_install_teardown(self):
        """
        Kills the profile PID, removes the PID file and removes the profile from persistence.
        """
        try:
            process.kill_process_id(self.profile.pid, signal.SIGINT)
        except Exception as e:
            log.logger.debug("Failed to kill pid, may have already been killed, continuing teardown: {0}"
                             .format(e.message))
        finally:
            self.profile.remove()


class ProfileDaemon(UtilitiesDaemon):
    """
    Overrides Utilities daemon to store the pid on the remote MS instead of local host
    """

    def __init__(self, identifier, profile, *args, **kwargs):
        """

        :param identifier: identifier for the daemon, used for logs and pickled object
        :type identifier: str
        :param profile: Subclass to be used as a callable
        :type profile: `enmutils_int.lib.Profile`
        :param args: __builtin__ list
        :type args: list
        :param kwargs: __builtin__ dict
        :type kwargs: dict
        """
        self.profile_ident_file_path = profile.ident_file_path
        self.profile = profile
        self.check_for_existing_process(identifier)
        super(ProfileDaemon, self).__init__(identifier, profile, *args, **kwargs)

    def _raise_if_running(self):
        """
        :raises WorkloadVMDetected: daemon process is being spawned directly on an LMS when workloadVM is available
        :raises ProfileAlreadyRunning: if an existing process is detected
        """
        vm_key = 'WORKLOAD_VM'
        cmd = shell.Command('cat ~/.bashrc | grep -i {0}'.format(vm_key))
        response = shell.run_local_cmd(cmd)
        if cache.is_host_ms() and vm_key in response.stdout:
            raise WorkloadVMDetected('Cannot start profile: {0} on LMS when Workload VM is detected.'
                                     .format(self.profile.NAME))
        if filesystem.does_file_exist(self.profile_ident_file_path):
            pid = self.get_pid()
            log.logger.debug("Checking if process {0} is already running".format(pid))
            if pid and process.is_pid_running(str(pid)):
                if self.profile.state and self.profile.state != "COMPLETED":
                    raise ProfileAlreadyRunning('Profile {0} deemed to be already running as pid file still exists: {1}'
                                                .format(self.profile.NAME, self.profile_ident_file_path), self.profile.pid)
            else:
                log.logger.debug("PID file found, but the process is not currently running. Cleaning up!")
                filesystem.delete_file(self.profile_ident_file_path)

    @staticmethod
    def check_for_existing_process(profile_name):
        """
        Update the active profiles list at start up to prevent duplicates starting

        :param profile_name: Name of the profile to confirm is not already running
        :type profile_name: str

        :raises ProfileAlreadyRunning: if an existing process is detected
        """
        cmd = "pgrep -f '{0} {1}'".format(profile_name.upper(), profile_name.lower())
        response = shell.run_local_cmd(cmd)
        if response.ok:
            raise ProfileAlreadyRunning("Failed to start profile duplicate process found::\n{}."
                                        .format(response.stdout), pid=response.stdout)
