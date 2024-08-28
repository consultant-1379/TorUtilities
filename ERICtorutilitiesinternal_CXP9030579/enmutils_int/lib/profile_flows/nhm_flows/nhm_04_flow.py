from enmutils_int.lib.profile_flows.nhm_flows.nhm_concurrent_users_flow import NhmConcurrentUsersFlow


class Nhm04(NhmConcurrentUsersFlow):
    """
    Class to run the flow for NHM_04 profile
    """

    def execute_flow(self):
        """
        Executes the flow of NHM_04 profile

        """

        self.execute_profile_flow()
