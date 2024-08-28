from enmutils_int.lib.parameter_management import temporary_query_for_mo_class_mapping
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow

SEARCH_QUERY = "select all objects of type interfaces$$interface from node {0}"


class ParMgt04Flow(GenericFlow):
    def execute_flow(self):
        """
        Executes the flow for the profile
        """
        users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
        nodes = self.get_nodes_list_by_attribute(node_attributes=["node_name"])
        self.state = "RUNNING"
        while self.keep_running():
            self.sleep_until_time()
            self.create_and_execute_threads(zip(users, nodes), len(users), args=[self])

    @staticmethod
    def task_set(worker, profile):
        """
        Task set for use with thread queue

        :type worker: list
        :param worker: list of tuples of user and corresponding nodes to be searched
        :type profile: `flowprofile.FlowProfile`
        :param profile: Profile to add errors to
        """
        user, node = worker
        try:
            temporary_query_for_mo_class_mapping(user, SEARCH_QUERY.format(node.node_name))
        except Exception as e:
            profile.add_error_as_exception(e)
