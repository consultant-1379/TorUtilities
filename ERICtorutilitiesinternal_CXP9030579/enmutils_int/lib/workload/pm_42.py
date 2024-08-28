from enmutils_int.lib.profile_flows.pm_flows.pmcelltraceprofile import PmCelltraceProfile


class PM_42(PmCelltraceProfile):
    """
    Use Case ID:        PM_42
    Slogan:             LTE RadioNode Cell Trace Recording Subscription & File Collection (CBS)
    """

    NAME = "PM_42"

    def run(self):
        self.execute_flow(netex_query='select managedelement where neType={node_type} '
                                      'and managedelement has child eNodeBFunction')


pm_42 = PM_42()
