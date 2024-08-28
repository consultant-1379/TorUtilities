from time import time

from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.nhm import NhmKpi, sleep_until_profile_persisted, wait_for_nhm_setup_profile, SETUP_PROFILE
from enmutils_int.lib.profile_flows.nhm_flows.nhm_flow_profile import NhmFlowProfile
from requests.exceptions import HTTPError


class Nhm12(NhmFlowProfile):
    """
    Class to run the flow for NHM_12 profile
    """

    def __init__(self, *args, **kwargs):
        self.nodes_verified_on_enm = []
        super(Nhm12, self).__init__(*args, **kwargs)

    def allocate_nodes_from_other_profile(self, profile_name, node_type):
        """
        Get list of nodes allocated to other profile then allocate subset of those nodes to this profile

        :return: List of Node objects allocated to this profile
        :rtype: list
        """
        setup_profile_nodes = self.get_allocated_nodes(profile_name)
        nodes_in_setup_profile = [node for node in setup_profile_nodes if node.primary_type == node_type and
                                  node.managed_element_type == 'ENodeB' or node.primary_type in ['ERBS']]
        nodes_to_be_used_by_this_profile = nodes_in_setup_profile[:self.NODES[node_type]]
        self.allocate_specific_nodes_to_profile(nodes_to_be_used_by_this_profile)

        return self.get_nodes_list_by_attribute(node_attributes=['node_id', 'poid', 'primary_type'])

    def execute_flow(self):
        """
        Executes the flow of NHM_12 profile
        """
        sleep_until_profile_persisted(SETUP_PROFILE)
        wait_for_nhm_setup_profile()
        self.state = "RUNNING"

        user = self.create_profile_users(1, getattr(self, 'USER_ROLES', ['NHM_Administrator']))[0]

        allocated_nodes = self.allocate_nodes_from_other_profile(SETUP_PROFILE, "RadioNode")

        if allocated_nodes:
            kpi_name = "NHM12KPI{0}".format(int(time()))
            nhm_12_kpi = NhmKpi(user, kpi_name, reporting_objects=['eNodeBFunction'], nodes=allocated_nodes,
                                node_types=list(set([node.primary_type for node in allocated_nodes])),
                                threshold_value=3, threshold_domain="LESS_THAN")

            try:
                nhm_12_kpi.remove_kpis_by_pattern_new(user, "NHM12")
                nhm_12_kpi.create()
                self.teardown_list.append(NhmKpi(user=user, name=kpi_name))
                nhm_12_kpi.activate()
            except HTTPError as e:
                self.add_error_as_exception(
                    EnvironError("Error occurred during NHM_12 KPI creation msg: {0}".format(e)))
            else:
                log.logger.info('NHM 12 Profile has completed with sucessfuly created KPI: {0}'.format(kpi_name))

        else:
            self.add_error_as_exception(EnvironError(
                'No ENodeB Radionodes/ERBS allocated. Profile needs to use subset of Radionodes/ERBS assigned to setup'
                ' profile: {0}'.format(SETUP_PROFILE)))
