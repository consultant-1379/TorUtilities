from enmutils.lib import log
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.services.deploymentinfomanager_adaptor import get_pib_value_on_enm, update_pib_parameter_on_enm


class Fm31(GenericFlow):

    def execute_flow(self):
        """
        execute the flow for checking and updating the alarm overload protection parameters
        """
        parameters = self.PARAMETERS
        self.state = 'RUNNING'
        for parameter, expected_value in parameters:
            try:
                actual_value = get_pib_value_on_enm(self.SERVICE, parameter)
                if actual_value != expected_value:
                    log.logger.info('The value of the parameter {0} is {1}'.format(parameter, actual_value))
                    log.logger.info('Updating the parameter value to the correct value {0}'.format(expected_value))
                    update_pib_parameter_on_enm(self.SERVICE, parameter, expected_value)
                else:
                    log.logger.info('The value of the parameter {0} is as expected {1}'.format(parameter, actual_value))
            except Exception as e:
                self.add_error_as_exception(e)
