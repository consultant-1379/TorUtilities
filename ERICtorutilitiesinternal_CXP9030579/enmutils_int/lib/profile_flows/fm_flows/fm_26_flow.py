from enmutils.lib import log
from enmutils_int.lib.fm import get_alarm_hist
from enmutils_int.lib.profile_flows.flowprofile import FlowProfile
from enmutils_int.lib.services.deploymentinfomanager_adaptor import update_pib_parameter_on_enm


class Fm26(FlowProfile):
    """
    Class for FM_26 Alarm History functions that need access to the profile object in Alarm History profiles
    """

    MAX_ALARMS = [120000, 10000]

    def alarm_history_cli_capability_main_flow(self):
        """
        This function executes the main flow for FM_26
        """
        users = []
        try:
            users = self.create_users(self.NUM_USERS, self.USER_ROLES, fail_fast=False, safe_request=True,
                                      retry=True)[0]
        except Exception as e:
            self.add_error_as_exception(e)

        self.state = "RUNNING"
        while self.keep_running():

            self.sleep_until_time()
            if users:
                self.increase_max_alarms()
                try:
                    # Execute a number of tasksets for each user
                    get_alarm_hist(self.TIME_PERIOD_IN_MIN, user=users)
                except Exception as e:
                    self.add_error_as_exception(e)
                self.decrease_max_alarms()

    def increase_max_alarms(self):
        """
        This function increases the max number of alarms in the CLI
        """
        try:
            update_pib_parameter_on_enm(enm_service_name="fmserv",
                                        pib_parameter_name="maxNumberOfAlarmsInCli",
                                        pib_parameter_value=str(self.MAX_ALARMS[0]))
            log.logger.debug("Successfully increased the maximum number of alarms in the CLI")
        except Exception as e:
            self.add_error_as_exception(e)

    def decrease_max_alarms(self):
        """
        This function reduces the max number of alarms in the CLI
        """
        try:
            update_pib_parameter_on_enm(enm_service_name="fmserv",
                                        pib_parameter_name="maxNumberOfAlarmsInCli",
                                        pib_parameter_value=str(self.MAX_ALARMS[1]))
            log.logger.debug("Successfully reduced the maximum number of alarms in the CLI")
        except Exception as e:
            self.add_error_as_exception(e)
