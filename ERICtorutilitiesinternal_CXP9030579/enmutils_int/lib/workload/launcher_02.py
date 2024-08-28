from enmutils_int.lib.profile_flows.launcher_flows.launcher_flow import LauncherFlow02


class LAUNCHER_02(LauncherFlow02):
    """
    Use Case id:        Launcher_02
    Slogan:             ENM Launcher-Display Groups and Applications
    """

    NAME = "LAUNCHER_02"

    def run(self):
        self.execute_flow()


launcher_02 = LAUNCHER_02()
