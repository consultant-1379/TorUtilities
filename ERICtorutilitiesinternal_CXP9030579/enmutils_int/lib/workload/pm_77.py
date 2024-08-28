from enmutils_int.lib.profile_flows.pm_flows.pmbscrecordingsprofile import PmBscRecordingsProfile


class PM_77(PmBscRecordingsProfile):
    """
    Use Case ID:    PM_77
    Slogan:         GSM BSC recording
    """
    NAME = "PM_77"

    def run(self):
        self.execute_flow()


pm_77 = PM_77()
