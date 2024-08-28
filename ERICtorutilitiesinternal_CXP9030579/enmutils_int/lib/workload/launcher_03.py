from enmutils_int.lib.profile_flows.launcher_flows.launcher_flow import LauncherFlow03


class LAUNCHER_03(LauncherFlow03):
    """
    Use Case id:        Launcher_03
    Slogan:             ENM Launcher-Favorite and un- favorite Applications.
    """

    NAME = "LAUNCHER_03"

    def run(self):

        self.execute_flow()


launcher_03 = LAUNCHER_03()
