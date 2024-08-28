from enmutils_int.lib.profile_flows.pm_flows.pmprofile import PmProfile


class Pm17Profile(PmProfile):

    def execute_flow(self):
        """
        Main flow for PM_17
        """

        self.state = "RUNNING"

        while self.keep_running():
            try:
                for retention_param in self.PM_NBI_RETENTION_PARAMETERS.values():
                    self.check_pmic_retention_period(retention_param)
            except Exception as e:
                self.add_error_as_exception(e)
            self.sleep()
