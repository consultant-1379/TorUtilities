import time
from enmutils.lib import log
from enmutils.lib.headers import JSON_SECURITY_REQUEST
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.nhm import get_nhm_nodes
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.nhm_rest_nbi import NhmRestNbiKpi, NHM_REST_NBI_KPI_OPERATION
from enmutils_int.lib.profile_flows.nhm_rest_nbi_flows.nhm_rest_nbi_common_flow import NhmRestNbiFlow


class NhmNbi05Flow(GenericFlow):
    """
        Class to run the flow for NHM_REST_NBI_05 profile
    """
    def __init__(self, *args, **kwargs):
        self.FLAG = ""
        super(NhmNbi05Flow, self).__init__(*args, **kwargs)

    def _clean_system_nhm_rest_nbi(self, user):
        """
        Deletes Node Level KPIs created by NHM_REST_NBI_SETUP
        """
        try:
            NhmRestNbiKpi.remove_kpis_nhm_rest_nbi_05_by_pattern(user=user)
        except Exception as e:
            self.add_error_as_exception(e)
        log.logger.debug("KPI cleaned down system. Removed node level KPIs created by profile")

    def read_set_of_ten_kpi(self, user, node_level_kpis):
        """
        Each user reading 10 node level kpis

        :params user: user to make requests
        :type user: list
        :params node_level_kpis: The List of node with correct POIDs to use for NHM
        :type node_level_kpis: list

        """
        log.logger.debug("User {0} is started Reading KPI".format(user))
        for kpis in node_level_kpis:
            log.logger.debug("kpi name {0} and the kpi id {1}".format(kpis['name'], kpis['id']))
            response = user.get(NHM_REST_NBI_KPI_OPERATION.format(id=kpis['id']), headers=JSON_SECURITY_REQUEST)
            if response.ok:
                log.logger.debug("User {0} is read KPI {1} successfully".format(user, kpis['name']))
            else:
                raise EnvironError('Unable to read kpi')

    def read_nhm_rest_nbi_05_kpi(self, user):
        """
        Five Users trying to Read KPI
        :params user: user to make requests
        :type user: list
        """
        node_level_kpis = [kpi for kpi in NhmRestNbiFlow().get_list_all_kpis(user[0]) if 'NHM REST NBI 05' in kpi['name']]
        for i in xrange(5):
            start = i * 10
            end = (i + 1) * 10
            self.read_set_of_ten_kpi(user[i], node_level_kpis[start:end])

    def execute_flow(self):
        """
        Executes the flow of NHM_REST_NBI_05
        """
        self.state = "RUNNING"
        while self.keep_running():
            self.sleep_until_day()
            user = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
            allocated_nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "poid", "primary_type"])
            nodes_verified_on_enm = get_nhm_nodes(self, user[0], allocated_nodes)
            self._clean_system_nhm_rest_nbi(user[0])
            if nodes_verified_on_enm:
                try:
                    nodes = [node for node in nodes_verified_on_enm if
                             node.primary_type not in self.UNSUPPORTED_TYPES_NODE_LEVEL_KPI]
                    if nodes:
                        for i in xrange(self.NUM_KPIS_01):
                            kpi_name = "{0} KPI {1}".format(self.identifier.replace('_', " ").replace('-', " "), i)
                            self.create_node_level_kpi(user[0], kpi_name, nodes)
                        time.sleep(5)
                        self.read_nhm_rest_nbi_05_kpi(user)
                        time.sleep(5)
                        self._clean_system_nhm_rest_nbi(user[0])
                except Exception as e:
                    self.add_error_as_exception(e)
            else:
                self.add_error_as_exception(EnvironError("No nodes verified on ENM."))

    def create_node_level_kpi(self, user, kpi_name, nodes):
        """
        Create nhm rest nbi 05 node level KPI
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
