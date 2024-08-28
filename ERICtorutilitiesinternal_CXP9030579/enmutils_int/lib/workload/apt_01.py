from enmutils_int.lib.profile_flows.stkpi_apt_flows.stkpi_flow import STKPIFlow


class APT_01(STKPIFlow):
    """
    Use Case ID:        APT_01
    Dummy profile to ring-fence nodes for the Automated Performance Test (APT) loop KPI Testcases
    Template config file available in: /home/enmutils/stkpi_config.py
    """

    NAME = "APT_01"

    def run(self):
        self.execute_flow()


apt_01 = APT_01()
