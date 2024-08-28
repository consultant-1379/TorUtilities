from enmutils_int.lib.profile_flows.pm_flows.pmuetrprofile import PmUETRProfile


class PM_47(PmUETRProfile):
    """
    Use Case ID:    PM_47
    Slogan:         UETR Event file Collection
    """
    NAME = "PM_47"

    def run(self):
        self.execute_flow()


pm_47 = PM_47()
