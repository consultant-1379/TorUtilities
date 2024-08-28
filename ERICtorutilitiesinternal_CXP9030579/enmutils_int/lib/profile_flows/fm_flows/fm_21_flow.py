from enmutils_int.lib.profile_flows.flowprofile import FlowProfile
from enmutils.lib.enm_node_management import FmManagement


class Fm21(FlowProfile):
    """
    Class for FM_21 Fm full network synchronization
    """

    def execute_flow_fm_21(self):
        """
        This function executes the main flow for FM_21
        """
        user = self.create_users(self.NUM_USERS, self.USER_ROLES, fail_fast=False, retry=True)[0]
        fmManagement = FmManagement(user=user)

        self.state = "RUNNING"

        while self.keep_running():

            self.sleep_until_time()

            try:
                fmManagement.synchronize()
            except Exception as e:
                self.add_error_as_exception(e)
