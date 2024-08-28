import time

from enmutils.lib import log
from enmutils.lib.thread_queue import ThreadQueue
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow
from enmutils_int.lib.shm_backup_jobs import BackupJobCPP
from enmutils_int.lib.shm import RestoreJob
from enmutils_int.lib.shm_delete_jobs import DeleteBackupOnNodeJobCPP
from enmutils_int.lib.shm_utilities import SHMUtils


class ShmRestoreFlow(ShmFlow):

    @staticmethod
    def restore_task_set(node, user, file_name):
        """
        Executes rollback command for each node
        :param node: node_id of node instance to be used for executing command in enm's script engine
        :type node: `load_node.Node`
        :param user: User object to be used to make requests
        :type user: `enm_user_2.User`
        :param file_name: file name provided while executing backup job
        :type file_name: str
        :raises EnmApplicationError: when failed to execute rollback command
        """
        cmd_subnet = 'cmedit get {subnetwork},MeContext={node_id} ConfigurationVersion.startableConfigurationVersion'
        cmd_backup_name = ('cmedit action {subnetwork},MeContext={node_id},ManagedElement=1,SwManagement=1, '
                           'ConfigurationVersion=1 setStartable.(configurationVersionName={backup_name})')
        cmd_rollback = ('cmedit action {subnetwork},MeContext={node_id}, ManagedElement=1 '
                        'manualRestart.(restartRank="RESTART_COLD", restartReason="PLANNED_RECONFIGURATION", '
                        'restartInfo="Restart for CV restore") --force')
        node_commands = [cmd_subnet.format(subnetwork=node.subnetwork, node_id=node.node_id),
                         cmd_backup_name.format(subnetwork=node.subnetwork, node_id=node.node_id, backup_name=file_name),
                         cmd_rollback.format(subnetwork=node.subnetwork, node_id=node.node_id)]
        for command in node_commands:
            response = user.enm_execute(command)
            if "1 instance(s)" not in response.get_output():
                raise EnmApplicationError("Failed while executing rollback command: {0}".format(command))

    def create_restore_job(self, user, synced_nodes):
        """
        Creates backup and restore job for shm 18, 26 profiles
        :param user: User object to be used to make requests
        :type user: `enm_user_2.User`
        :param synced_nodes: List of filtered synchronised nodes allocated to the profile
        :type synced_nodes: list
        :raises EnvironError: when there are no available synced nodes in pool
        """
        try:
            if synced_nodes:
                if self.NAME == "SHM_26":
                    delayed_nodes = synced_nodes[0:len(synced_nodes) / 2]
                    SHMUtils.execute_restart_delay(delayed_nodes)
                # Create a shm backup job instance
                backup_file_name = self.NAME + "_restore_before_" + self.timestamp_str
                schedule_time_strings, shm_schedule_time_strings = self.get_schedule_time_strings()
                backup_job = BackupJobCPP(user=user, nodes=synced_nodes, description=self.BACKUP_DESCRIPTION,
                                          platform="CPP", repeat_count="0", file_name=backup_file_name,
                                          profile_name=self.NAME,
                                          shm_schedule_time_strings=shm_schedule_time_strings,
                                          schedule_time_strings=schedule_time_strings)
                delete_backup_from_node = DeleteBackupOnNodeJobCPP(user=user, nodes=synced_nodes,
                                                                   file_name=backup_file_name,
                                                                   remove_from_rollback_list="TRUE", platform="CPP",
                                                                   profile_name=self.NAME,
                                                                   shm_schedule_time_strings=shm_schedule_time_strings,
                                                                   schedule_time_strings=schedule_time_strings)
                # Create a shm restore job instance
                restore_job = RestoreJob(user=user, nodes=synced_nodes, description=self.RESTORE_DESCRIPTION,
                                         file_name=backup_file_name, profile_name=self.NAME)
                log.logger.debug("Sleeping for 3secs before initiating another backup job instance")
                time.sleep(3)
                # Create a shm backup job instance
                backup_startable_file_name = self.NAME + "_restore_after_" + self.timestamp_str
                backup_startable = BackupJobCPP(user=user, nodes=synced_nodes, description=self.BACKUP_DESCRIPTION,
                                                repeat_count="0", file_name=backup_startable_file_name,
                                                set_as_startable=True, profile_name=self.NAME,
                                                shm_schedule_time_strings=shm_schedule_time_strings,
                                                schedule_time_strings=schedule_time_strings)
                backup_job.create()
                backup_startable.create()
                delete_backup_from_node.create()
                restore_job.create()
                restore_job.wait_time_for_job_to_complete(max_iterations=2, time_to_sleep=1800)
                tq = ThreadQueue(synced_nodes, num_workers=len(synced_nodes), func_ref=self.restore_task_set,
                                 args=[user, backup_startable_file_name])
                tq.execute()
            else:
                raise EnvironError("No available synced nodes, can't proceed further job execution")
        except Exception as e:
            self.add_error_as_exception(e)

    def execute_flow(self):
        """
        Executes Restore Flow for Shm 18 and 26 profiles
        """
        self.state = "RUNNING"
        user = self.create_profile_users(1, roles=["Cmedit_Administrator", "Shm_Administrator"])[0]
        while self.keep_running():
            if self.NAME == "SHM_26":
                synced_nodes = self.select_nodes_based_on_profile_name(user)
                self.create_restore_job(user, synced_nodes)
                break
            elif self.NAME == "SHM_18":
                synced_nodes = self.select_required_number_of_nodes_for_profile(user, "day")
                self.create_restore_job(user, synced_nodes)
                self.exchange_nodes()


class Shm18Flow(ShmRestoreFlow):

    BACKUP_DESCRIPTION = 'Backup created for rollback, restore on 100 DU nodes each Sunday'
    RESTORE_DESCRIPTION = 'Performs restore on 100 DU nodes each Sunday'


class Shm26Flow(ShmRestoreFlow):

    BACKUP_DESCRIPTION = 'Performs delayed backup on 100 ERBS nodes'
    RESTORE_DESCRIPTION = 'Performs delayed restore on 100 ERBS nodes'
