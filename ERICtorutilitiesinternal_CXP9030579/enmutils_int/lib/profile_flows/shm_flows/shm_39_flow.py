from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow
from enmutils_int.lib.shm_backup_jobs import BackupJobBSC
from enmutils_int.lib.shm_delete_jobs import DeleteBackupOnNodeJobBSC


class Shm39Flow(ShmFlow):

    REPEAT_COUNT = "0"
    DESCRIPTION = "Performs backup on 5 BSC nodes/10 BSC components in a single job "
    TLS_FLAG = False

    def execute_flow(self):
        """
        Executes the backup profile flow
        """
        self.state = "RUNNING"
        user = self.create_profile_users(self.NUM_USERS, roles=self.USER_ROLES)[0]
        while self.keep_running():
            try:
                synced_nodes = self.select_required_number_of_nodes_for_profile(user, "day")
                schedule_time_strings, shm_schedule_time_strings = self.get_schedule_time_strings()
                if synced_nodes:
                    try:
                        if not self.TLS_FLAG:
                            self.download_tls_certs([user])
                            self.TLS_FLAG = True
                        backup_start_time = self.get_current_epoch_time_in_milliseconds
                        log.logger.debug("Time recorded  before backup starts: {0}".format(backup_start_time))
                        backup_job = BackupJobBSC(user=user, nodes=synced_nodes, repeat_count=self.REPEAT_COUNT,
                                                  description=self.DESCRIPTION, profile_name=self.NAME,
                                                  shm_schedule_time_strings=shm_schedule_time_strings,
                                                  schedule_time_strings=schedule_time_strings)
                        delete_backup_on_node = DeleteBackupOnNodeJobBSC(user=user, nodes=synced_nodes,
                                                                         remove_from_rollback_list="TRUE",
                                                                         backup_start_time=backup_start_time,
                                                                         profile_name=self.NAME,
                                                                         shm_schedule_time_strings=shm_schedule_time_strings,
                                                                         schedule_time_strings=schedule_time_strings)
                        self.execute_backup_jobs(backup_job, delete_backup_on_node, user, enable_node_sync=True)
                    except Exception as e:
                        self.add_error_as_exception(e)
                else:
                    self.add_error_as_exception(EnvironError('No nodes available to create backup job'))
                self.exchange_nodes()
            except Exception as e:
                self.add_error_as_exception(e)
