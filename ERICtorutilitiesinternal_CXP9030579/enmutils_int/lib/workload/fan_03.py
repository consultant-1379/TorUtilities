from enmutils_int.lib.profile_flows.common_flows.common_flow import PlaceHolderFlow


class FAN_03(PlaceHolderFlow):
    """
    Deprecated 23.17 Delete 24.12 JIRA:ENMRTD-23897
    """
    NAME = "FAN_03"

    def run(self):  # pylint: disable=unused-argument
        pass


fan_03 = FAN_03()
