from enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles import FileAccessNbiProfile


class FAN_14(FileAccessNbiProfile):
    """
    Use Case ID:    FAN_14
    Slogan:    PM NBI profile for cENM with PM/3PP as NBI.
    """
    NAME = "FAN_14"

    def run(self):
        self.execute_flow()


fan_14 = FAN_14()
