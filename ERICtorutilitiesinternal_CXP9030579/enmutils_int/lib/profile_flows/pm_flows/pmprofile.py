from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils_int.lib.profile_flows.flowprofile import FlowProfile
from enmutils_int.lib.services.deploymentinfomanager_adaptor import get_pib_value_on_enm


class PmProfile(FlowProfile):
    """
    PM profile flows superclass
    """

    def show_errored_threads(self, tq, n_threads, error_type):
        """
        Checks whether any thread process has failed

        :param tq; type: ThreadQueue obj
        :param n_threads; type: Int. Number of thread processes ran
        :param error_type; type: EnmUtilsException obj. Error type to raise.

        :return Void.
        """
        errors = 0
        for entry in tq.work_entries:
            if entry.exception_raised:
                errors += 1
        if errors:
            msg = "Errors for {0}/{1} thread(s). Check the profiles' logs.".format(errors, n_threads)
            self.add_error_as_exception(error_type(msg))

    def check_pmic_retention_period(self, pib_parameter_info):
        """
        Check whether the given PMIC pib parameter retention periods are set to expected default values.

        :param pib_parameter_info: Contains parameter name and its expected default retention value.
        :type pib_parameter_info: tuple

        """
        log.logger.debug("Attempting to check if the PMIC retention period for pib parameter: {0} matches the expected "
                         "default value of {1} minutes.".format(pib_parameter_info[0], pib_parameter_info[1]))

        pib_parameter, pib_default_retention_time = pib_parameter_info

        pib_value = get_pib_value_on_enm("pmserv", pib_parameter)

        if pib_value:
            if str(pib_default_retention_time) == pib_value:
                log.logger.debug("The Retention period for '{pib_parameter}' of '{expected_value}' was correct."
                                 .format(pib_parameter=pib_parameter, expected_value=pib_parameter_info[1]))
            else:
                self.add_error_as_exception(EnvironError(
                    "The '{pib_parameter}' retention period of: '{enm_retention_period}' minutes does not match the "
                    "expected default of: '{pib_default_retention_time}' minutes."
                    .format(pib_parameter=pib_parameter, enm_retention_period=pib_value,
                            pib_default_retention_time=pib_default_retention_time)))
        else:
            self.add_error_as_exception(EnmApplicationError("Could not get the value of the '{pib_parameter}'."
                                                            .format(pib_parameter=pib_parameter)))
