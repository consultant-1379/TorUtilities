from enmutils_int.lib.profile_flows.launcher_flows.launcher_flow import LauncherFlow01


class LAUNCHER_01(LauncherFlow01):
    """
    Use Case id:        Launcher_01
    Slogan:             ENM Launcher-Display Actions
    """

    NAME = "LAUNCHER_01"

    def run(self):
        self.execute_flow()


launcher_01 = LAUNCHER_01()
