from enmutils_int.lib.profile_flows.common_flows.common_flow import PlaceHolderFlow


class MIGRATION_02(PlaceHolderFlow):
    """
    Use Case ID:        Migration_02
    Slogan:             Number of migrated users
    """
    NAME = "MIGRATION_02"

    def run(self):
        self.execute_flow()


migration_02 = MIGRATION_02()
