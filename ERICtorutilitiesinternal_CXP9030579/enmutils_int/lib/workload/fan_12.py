from enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles import FileAccessNbiProfile


class FAN_12(FileAccessNbiProfile):
    """
    Use Case ID:    FAN_12
    Slogan:    PM NBI profile for cENM with PM/3PP as NBI.
    """
    NAME = "FAN_12"

    def run(self):
        self.execute_flow()


fan_12 = FAN_12()
