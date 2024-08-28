from enmutils_int.lib.profile_flows.fan_flows.file_access_nbi_profiles import FileAccessNbiProfile


class FAN_13(FileAccessNbiProfile):
    """
    Use Case ID:    FAN_13
    Slogan:    PM NBI profile for cENM with PM/3PP as NBI.
    """
    NAME = "FAN_13"

    def run(self):
        self.execute_flow()


fan_13 = FAN_13()
