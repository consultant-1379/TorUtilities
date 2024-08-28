import time
from enmutils.lib import log
from enmutils_int.lib.nhm import NhmKpi
from enmutils_int.lib.nhm import get_nhm_nodes
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow


class Nhm14Flow(GenericFlow):
    """
    Class to run the flow for NHM_14 profile
    """

    def execute_flow(self):
        """
        Runs the flow of NHM_14 profile which creates 25 user defined cell level KPIs
        """
        user = self.create_profile_users(self.NUM_OPERATORS, self.OPERATOR_ROLE)[0]
        self.state = "RUNNING"
        nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "poid"])
        nodes_verified_on_enm = get_nhm_nodes(self, user, nodes)
        reporting_objects = self.REPORTING_OBJECT
        counters = NhmKpi.get_counters_specified_by_nhm(reporting_objects,
                                                        ne_type=self.SUPPORTED_TYPES_CUSTOM_CELL_LEVEL_KPI[0])
        for i in xrange(self.NUMBER_OF_KPIS):
            try:
                kpi_name = "{0}_KPI_{1}".format(self.identifier, i)
                kpi = NhmKpi(user, kpi_name, nodes_verified_on_enm, reporting_objects=reporting_objects, counters=counters,
                             node_types=self.SUPPORTED_TYPES_CUSTOM_CELL_LEVEL_KPI)
                kpi.create()
                self.teardown_list.append(NhmKpi(user=user, name=kpi_name))
                time.sleep(1)
            except Exception as e:
                self.add_error_as_exception(e)
        log.logger.info('Successfully created {0} custom cell level KPIs.'.format(self.NUMBER_OF_KPIS))
