from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.nhm import get_nhm_nodes
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.nhm_rest_nbi import NhmRestNbiKpi


class NhmRestNbiSetup(GenericFlow):
    """
    Class to run the flow for NHM_REST_NBI_SETUP profile
    """

    def __init__(self, *args, **kwargs):
        self.FLAG = ""
        super(NhmRestNbiSetup, self).__init__(*args, **kwargs)

    def _clean_system_nhm_rest_nbi(self, user):
        """
        Deletes Node Level KPIs created by NHM_REST_NBI_SETUP
        """
        try:
            NhmRestNbiKpi.remove_kpis_by_pattern(user=user)
        except Exception as e:
            self.add_error_as_exception(e)
        log.logger.debug("KPI cleaned down system. Removed node level KPIs created by profile")

    def execute_flow(self):
        """
        Executes the flow of NHM_REST_NBI_SETUP test cases
        """
        self.state = "RUNNING"
        user = self.create_profile_users(1, self.USER_ROLES)[0]
        allocated_nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "poid", "primary_type"])
        nodes_verified_on_enm = get_nhm_nodes(self, user, allocated_nodes)
        self._clean_system_nhm_rest_nbi(user)

        if nodes_verified_on_enm:
            try:
                nodes = [node for node in nodes_verified_on_enm if
                         node.primary_type not in self.UNSUPPORTED_TYPES_NODE_LEVEL_KPI]
                if nodes:
                    for i in xrange(self.NUM_KPIS_01):
                        kpi_name = "{0} KPI {1}".format(self.identifier.replace('_', " ").replace('-', " "), i)
                        self.create_and_activate_node_level_kpi(user, kpi_name, nodes)
            except Exception as e:
                self.add_error_as_exception(e)
            self.FLAG = 'COMPLETED'
        else:
            log.logger.error('No nodes verified on ENM. Setup failed to complete. NHM profiles will not execute!!!')
            self.add_error_as_exception(EnvironError("No nodes verified on ENM. Setup failed to complete. "
                                                     "NHM profiles will not execute!"))

    def create_and_activate_node_level_kpi(self, user, kpi_name, nodes):
        """
        Create and activate a node level KPI
        :param user: user to carry out requests
        :type user: enm_user_2.User
        :param kpi_name: kpi name of KPI to create
        :type kpi_name: str
        :param nodes: list of enm_node.Node objects
        :type nodes: list
        """
        kpi = NhmRestNbiKpi(user=user, kpi_name=kpi_name, nodes=nodes)
        kpi.create()
        self.teardown_list.append(NhmRestNbiKpi(user=user, kpi_name=kpi_name))
        kpi.activate()
