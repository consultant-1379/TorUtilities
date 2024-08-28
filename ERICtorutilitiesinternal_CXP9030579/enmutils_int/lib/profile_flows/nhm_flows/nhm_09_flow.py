from enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow import NhmConcurrentUsersFlow


class Nhm09(NhmConcurrentUsersFlow):

    def execute_flow(self):
        """
        Executes the flow of NHM_09 profile

        """

        self.execute_profile_flow()
