from enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow import CliMon01Flow


class CLI_MON_01(CliMon01Flow):
    """
    Use Case ID:        CLI_MON_01
    Slogan:             System Healthcheck
    """

    NAME = "CLI_MON_01"

    def run(self):
        self.execute_flow()


cli_mon_01 = CLI_MON_01()
