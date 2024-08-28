from datetime import datetime, timedelta
from enmutils_int.lib.profile_flows.flowprofile import FlowProfile
from enmutils.lib.exceptions import ScriptEngineResponseValidationError, EnmApplicationError
from enmutils.lib import log


class Fm11(FlowProfile):
    """
    Class for FM_11: Max open alarms using ENM CLI
    """

    COMMAND = 'alarm get * --begin {0} --count'

    def execute_flow_fm_11(self):
        """
        This function executes the main flow for FM_11
        @return: void
        """
        user = self.create_users(self.NUM_USERS, self.USER_ROLES, fail_fast=False, retry=True)[0]

        self.state = "RUNNING"

        while self.keep_running():
            time_span = 60 * 20

            while time_span >= 1:
                formatted_time = str((datetime.now() - timedelta(seconds=time_span)).strftime("%Y-%m-%dT%H:%M:%S"))
                command = self.COMMAND.format(formatted_time)
                try:
                    command_response = user.enm_execute(command)
                    log.logger.info("Response is: {0}".format(str(command_response.get_output()[-1])))
                except Exception as e:
                    self.add_error_as_exception(EnmApplicationError("Exception: {0}".format(e)))
                    break

                if any("Invalid value" in line for line in command_response.get_output()):
                    raise ScriptEngineResponseValidationError('Unable to execute command. Response was "%s"' %
                                                              (', '.join(command_response.get_output())),
                                                              response=command_response)
                # systematically narrows the time window until it has less than 10000 alarms.
                if any("Please narrow down the criteria" in line for line in command_response.get_output()):
                    log.logger.debug("{} alarms were returned. This is greater than the 10,000 limit. The time "
                                     "window will be reduced to bring the number of alarms below 10,000".format
                                     (str(command_response.get_output()[-1].split(':')[-1])))
                    if time_span <= 60 * 3:
                        time_span /= 2
                    else:
                        time_span -= 60 * 1
                else:
                    break
            self.sleep()
