from enmutils_int.lib.profile_flows.fmx_flows.fmx_01_flow import FMX01


class FMX_01(FMX01):
    """
    Use Case ID:        FMX_01
    Slogan:             FMX module Activation
    """

    NAME = 'FMX_01'

    def run(self):
        self.execute_fmx_01_flow()


fmx_01 = FMX_01()
