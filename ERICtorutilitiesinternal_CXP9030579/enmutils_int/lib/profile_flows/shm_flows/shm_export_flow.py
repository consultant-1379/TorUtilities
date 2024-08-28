from enmutils_int.lib.profile_flows.shm_flows.shm_flow import ShmFlow
from enmutils_int.lib.shm import SHMExport


class ShmExportFlow(ShmFlow):

    def execute_flow(self):
        """
        Executes Export Flow for Shm 19, 20 and 21 profiles
        """
        self.state = "RUNNING"
        user = self.create_profile_users(1, roles=["Cmedit_Administrator", "Shm_Administrator"])[0]
        nodes = self.get_nodes_list_by_attribute()
        while self.keep_running():
            self.sleep_until_day()
            try:
                export = SHMExport(user=user, nodes=nodes, export_type=self.EXPORT_TYPE)
                export.create()
            except Exception as e:
                self.add_error_as_exception(e)


class Shm19Flow(ShmExportFlow):

    EXPORT_TYPE = "HARDWARE"


class Shm20Flow(ShmExportFlow):

    EXPORT_TYPE = "SOFTWARE"


class Shm21Flow(ShmExportFlow):

    EXPORT_TYPE = "LICENSE"
