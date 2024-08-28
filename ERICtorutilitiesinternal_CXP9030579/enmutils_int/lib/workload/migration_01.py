from enmutils_int.lib.profile_flows.common_flows.common_flow import PlaceHolderFlow


class MIGRATION_01(PlaceHolderFlow):
    """
    Use Case ID:        Migration_01
    Slogan:             Size of Network Element batch
    """

    NAME = "MIGRATION_01"

    def run(self):
        self.execute_flow()


migration_01 = MIGRATION_01()
