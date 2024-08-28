
from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_flow import CmExportFlow
from enmutils.lib.enm_node_management import CmManagement


class CmExport23Flow(CmExportFlow):

    def execute_flow(self):
        """
        Supervises the Nodes for enm and then de-allocates them
        """
        nodes_list = self.get_nodes_list_by_attribute(node_attributes=['profiles', 'node_id'])
        try:
            cm_supervision_obj = CmManagement(node_ids=[node.node_id for node in nodes_list])
            cm_supervision_obj.supervise(timeout_seconds=self.TIMEOUT)
            self.update_profile_persistence_nodes_list(nodes_list)
        except Exception as e:
            self.add_error_as_exception(e)
        super(CmExport23Flow, self).execute_flow()
