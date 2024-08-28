from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib import node_pool_mgr
from enmutils_int.lib.common_utils import chunks
from enmutils_int.lib.helper_methods import generate_basic_dictionary_from_list_of_objects
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow
from enmutils_int.lib.shm_utility_jobs import ShmBSCBackUpCleanUpJob, ShmBackUpCleanUpJob


class Shm35Flow(ShmFlow):

    def execute_backup_and_cleanup_job(self, synced_nodes, nodes, user, platform):
        description = "Performs backup cleanup job on all available Nodes"
        if synced_nodes[0].primary_type == "BSC":
            job_name = "{0}_BackupHousekeepingJob_{1}_{2}".format(self.NAME, nodes[0].primary_type,
                                                                  self.timestamp_str)
            cleanup_job = ShmBSCBackUpCleanUpJob(user, nodes=synced_nodes, name=job_name,
                                                 description=description, platform=platform,
                                                 profile_name=self.NAME)
            cleanup_job.create()
        else:
            job_name = "{0}_Cleanup_job_{1}_{2}".format(self.NAME, nodes[0].primary_type,
                                                        self.timestamp_str)
            cleanup_job = ShmBackUpCleanUpJob(user, nodes=synced_nodes, name=job_name,
                                              description=description, platform=platform,
                                              profile_name=self.NAME)
            cleanup_job.create()

    @staticmethod
    def prepare_nodes_chunk(nodes, nodes_per_chunk, node_type):
        if nodes:
            node_chunks = chunks(nodes, nodes_per_chunk)
        else:
            node_chunks = []
            log.logger.debug("EnvironWarning: No available {0} nodes to start SHM House Keeping Job"
                             .format(node_type))
        return node_chunks

    def execute_flow(self):
        """
        Executes Shm_35 profile flow
        """
        self.state = "RUNNING"
        user = self.create_profile_users(1, roles=self.USER_ROLES)[0]
        nodes_per_chunk = self.NODES_PER_CHUNK
        while self.keep_running():
            self.sleep_until_day()
            try:
                total_nodes = self.get_nodes_list_by_attribute(
                    node_attributes=["node_id", "primary_type", "node_ip", "netsim", "poid", "simulation", "node_name"])
                nodes_dict = generate_basic_dictionary_from_list_of_objects(total_nodes, "primary_type")
                supported_nodes = ["ERBS", "RadioNode", "Router6672", "Router6675", "BSC"]
                nodes_platform = ["CPP", "ECIM", "ECIM", "ECIM", "AXE"]
                for node_index, node_type in enumerate(supported_nodes):
                    platform, nodes = nodes_platform[node_index], nodes_dict.get(node_type)
                    node_chunks = self.prepare_nodes_chunk(nodes, nodes_per_chunk, node_type)
                    for node_chunk in node_chunks:
                        started_nodes = self.get_started_annotated_nodes(user, node_chunk)
                        synced_nodes = node_pool_mgr.filter_unsynchronised_nodes(started_nodes)
                        if synced_nodes:
                            self.execute_backup_and_cleanup_job(synced_nodes, nodes, user, platform)
                        else:
                            self.add_error_as_exception(EnvironError('No available {0} synced nodes to start SHM House '
                                                                     'Keeping Job'.format(node_type)))
            except Exception as e:
                self.add_error_as_exception(e)
