import time

from enmutils.lib import log
from enmutils_int.lib.common_utils import chunks
from enmutils_int.lib.helper_methods import generate_basic_dictionary_from_list_of_objects
from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow


class Shm37Flow(ShmFlow):

    def execute_flow(self):
        """
        Executes the profile flow
        """
        self.state = "RUNNING"
        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]
        sleep_time_between_jobs = self.SLEEP_TIME_BETWEEN_JOBS
        nodes_per_chunk = self.NODES_PER_CHUNK
        node_primary_types = ["ERBS", "RadioNode", "Router6672", "Router_6672"]
        while self.keep_running():
            self.sleep_until_day()
            total_nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "primary_type"])
            profile_nodes = generate_basic_dictionary_from_list_of_objects(total_nodes, "primary_type")
            for node_type in node_primary_types:
                if node_type in profile_nodes:
                    node_chunks = chunks(profile_nodes[node_type], nodes_per_chunk)
                    for nodes in node_chunks:
                        synced_nodes = self.get_synced_nodes(nodes, len(nodes))
                        self.delete_inactive_upgrade_packages(user, synced_nodes, profile_name=self.NAME)
                        log.logger.info("Sleeping for {0} seconds after the previous delete inactive "
                                        "upgrade job is completed.".format(sleep_time_between_jobs))
                        time.sleep(sleep_time_between_jobs)
