from enmutils.lib import log
from enmutils.lib.exceptions import EnmApplicationError, EnvironWarning
from enmutils_int.lib.consistency_audit import create_audit_job, invoke_audit_job, poll_job_status
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow

REQUIRED_NODES = ["RNC01", "MSC01BSC01", "M01B01"]  # adding M01B01 for new NRM


class CA01Flow(GenericFlow):

    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)[0]
        self.state = 'RUNNING'
        while self.keep_running():
            self.sleep_until_next_scheduled_iteration()
            for node in self.get_available_nodes():
                self.create_invoke_poll_jobs_for_available_nodes(user, node)

    def get_available_nodes(self):
        """
        Fetches available nodes on the deployment from the list of required nodes

        :rtype: list
        :return: List of available nodes
        """
        available_nodes = [node.node_id for node in self.all_nodes_in_workload_pool(node_attributes=["node_id"])
                           if node.node_id in REQUIRED_NODES]
        if len(available_nodes) != len(REQUIRED_NODES):
            self.add_error_as_exception(EnvironWarning("Performing audit actions only for available node(s) - {0} "
                                                       "out of required nodes - {1}"
                                                       .format(available_nodes, REQUIRED_NODES)))
        else:
            log.logger.debug("All required nodes are available on the deployment - {0}".format(available_nodes))
        return available_nodes

    def create_invoke_poll_jobs_for_available_nodes(self, user, node):
        """
        Function to perform create, invoke and poll operations for required nodes

        :type user: `enm_user_2.User`
        :param user: User who will create, invoke and poll the jobs
        :type node: str
        :param node: Node on which audit actions are to be performed
        """
        try:
            job_name = "{0}_{1}_{2}".format(self.NAME, node, self.get_timestamp_str())
            create_response = create_audit_job(user, job_name, node)
            invoke_audit_job(user, create_response)
            poll_job_status(user, create_response, self.RETRIES, self.INTERVAL)
        except Exception as e:
            self.add_error_as_exception(EnmApplicationError("Error occurred while performing audit actions"
                                                            " for node {0}. Error: {1}".format(node, str(e))))
