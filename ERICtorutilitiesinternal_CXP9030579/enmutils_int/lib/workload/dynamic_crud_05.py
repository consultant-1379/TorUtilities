from enmutils_int.lib.profile_flows.dynamic_crud_flows.dynamic_crud_05_flow import DynamicCrud05Flow


class DYNAMIC_CRUD_05(DynamicCrud05Flow):
    """
    Use Case ID:    DYNAMIC_CRUD_05
    Slogan:         Dynamic CM NBI CRUD Create/Delete Patch Storms
    """
    NAME = "DYNAMIC_CRUD_05"

    def run(self):
        self.execute_flow()


dynamic_crud_05 = DYNAMIC_CRUD_05()
