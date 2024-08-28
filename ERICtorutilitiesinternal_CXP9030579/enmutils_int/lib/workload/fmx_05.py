from enmutils_int.lib.profile_flows.fmx_flows.fmx_05_flow import FMX05


class FMX_05(FMX05):
    """
    Use Case ID:        FMX_05
    Slogan:             FMX Maintenance Mode
    """

    NAME = 'FMX_05'

    def run(self):
        self.execute_fmx_05_flow()


fmx_05 = FMX_05()
