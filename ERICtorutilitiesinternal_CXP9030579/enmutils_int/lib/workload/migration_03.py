from enmutils_int.lib.profile_flows.common_flows.common_flow import PlaceHolderFlow


class MIGRATION_03(PlaceHolderFlow):
    """
    Use Case ID:        Migration_03
    Slogan:             No Disruption of Existing Management
    """

    NAME = "MIGRATION_03"

    def run(self):
        self.execute_flow()


migration_03 = MIGRATION_03()
