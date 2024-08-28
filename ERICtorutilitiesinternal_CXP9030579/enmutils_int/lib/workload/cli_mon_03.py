from enmutils_int.lib.profile_flows.cli_mon_flows.cli_mon_flow import CliMon03Flow


class CLI_MON_03(CliMon03Flow):
    """
    Use Case ID:        CLI_MON_03
    Slogan:             CM Sync Status
    """

    NAME = "CLI_MON_03"

    def run(self):
        self.execute_flow()


cli_mon_03 = CLI_MON_03()
