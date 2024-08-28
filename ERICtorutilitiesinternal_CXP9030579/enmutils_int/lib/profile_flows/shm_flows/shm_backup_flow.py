from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils.lib import arguments, multitasking
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow
from enmutils_int.lib.shm_backup_jobs import BackupJobCPP, BackupJobCOMECIM
from enmutils_int.lib.shm_utility_jobs import ShmBackUpCleanUpJob


class ShmBackupFlow(ShmFlow):

    def execute_flow(self):
        """
        Executes Shm Backup profile flow
        """
        self.state = "RUNNING"
        user = self.create_profile_users(1, roles=["Cmedit_Administrator", "Shm_Administrator"])[0]
        while self.keep_running():
            synced_nodes = self.select_required_number_of_nodes_for_profile(user, "time")
            if synced_nodes:
                nodes_per_batch = arguments.split_list_into_chunks(synced_nodes, self.NUM_NODES_PER_BATCH)
                distributed_nodes_per_batch = [(batch_num + 1, batch) for batch_num, batch in
                                               enumerate(nodes_per_batch)]
                multitasking.create_single_process_and_execute_task(execute_user_tasks, timeout=140 * 60,
                                                                    args=(self, distributed_nodes_per_batch,
                                                                          len(nodes_per_batch), user, 8100))
            else:
                self.add_error_as_exception(EnvironError('No nodes available to create backup job'))
            self.exchange_nodes()

    @staticmethod
    def task_set(batch_synced_nodes, user, profile):  # pylint: disable=arguments-differ
        """
        :type batch_synced_nodes: tuple
        :param batch_synced_nodes: tuple containing iter value and `enm_node.Node` objects
        :type user: `enm_user_2.User`
        :param user: ENM user used to create backup job
        :type profile: `lib.profile.Profile`
        :param profile: profile object used for function calls
        :raises EnmApplicationError: when flow goes to unexpected state
        """
        try:
            batch_num, synced_nodes = batch_synced_nodes
            description = 'Performs backup on {0} {1} nodes, in a single job'.format(len(synced_nodes),
                                                                                     synced_nodes[0].primary_type)
            schedule_time_strings, shm_schedule_time_strings = profile.get_schedule_time_strings()
            file_name = profile.timestamp_str + "_Batch" + str(batch_num)
            if profile.PLATFORM == "CPP":
                backup_job = BackupJobCPP(user=user, nodes=synced_nodes, description=description,
                                          file_name=file_name, repeat_count=profile.REPEAT_COUNT,
                                          profile_name=profile.NAME, schedule_time=shm_schedule_time_strings[0],
                                          platform=profile.PLATFORM, schedule_time_strings=schedule_time_strings,
                                          shm_schedule_time_strings=shm_schedule_time_strings, random_suffix=file_name)
                delete_backup_job = ShmBackUpCleanUpJob(user=user, nodes=synced_nodes, profile_name=profile.NAME,
                                                        random_suffix=file_name)
                profile.execute_backup_jobs(backup_job, delete_backup_job, user)
            elif profile.PLATFORM == "ECIM":
                backup_job = BackupJobCOMECIM(user=user, nodes=synced_nodes, repeat_count=profile.REPEAT_COUNT,
                                              description=description, profile_name=profile.NAME,
                                              schedule_time=shm_schedule_time_strings[0], platform=profile.PLATFORM,
                                              schedule_time_strings=schedule_time_strings,
                                              shm_schedule_time_strings=shm_schedule_time_strings,
                                              random_suffix=file_name)
                delete_backup_job = ShmBackUpCleanUpJob(user=user, nodes=synced_nodes, profile_name=profile.NAME,
                                                        file_name=profile.NAME + "_" + file_name, resolve_cv_name=True,
                                                        random_suffix=file_name, platform=profile.PLATFORM)
                profile.execute_backup_jobs(backup_job, delete_backup_job, user)
        except Exception as e:
            profile.add_error_as_exception(EnmApplicationError("Failed to run backup job, Exception: [{0}]"
                                                               .format(e.message)))


class Shm01Flow(ShmBackupFlow):

    PLATFORM = "CPP"
    REPEAT_COUNT = "0"


class Shm02Flow(ShmBackupFlow):

    PLATFORM = "ECIM"
    REPEAT_COUNT = "0"


def execute_user_tasks(profile, nodes_per_batch, num_nodes, user, wait_time):
    """
    Executes all the user tasks as a separate process (to reduce memory consumption)
    :param profile: SHM Profile object
    :type profile: enmutils_int.lib.profile.Profile
    :param nodes_per_batch: list of nodes per batch
    :type nodes_per_batch: list
    :param num_nodes: Number of nodes per batch
    :type num_nodes: int
    :param user: SHM User
    :type user: enm_user_2.User
    :param wait_time: Timeout for each thread
    :type wait_time: int
    """
    profile.create_and_execute_threads(workers=nodes_per_batch, thread_count=num_nodes, args=[user, profile],
                                       wait=wait_time, join=wait_time)
