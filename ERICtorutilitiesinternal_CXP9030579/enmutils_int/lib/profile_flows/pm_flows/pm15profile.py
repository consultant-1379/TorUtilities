from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.services.deploymentinfomanager_adaptor import get_pib_value_on_enm


class Pm15Profile(GenericFlow):

    def execute_flow(self):
        """
        Main flow for PM_15
        """
        self.state = "RUNNING"
        while self.keep_running():
            try:
                pib_value = get_pib_value_on_enm("pmserv", self.POLLING_AND_MASTER_RETENTION[0])
                if pib_value == str(self.POLLING_AND_MASTER_RETENTION[1]):
                    log.logger.debug("Value of pib parameter {0} is as expected: {1}".format(
                        self.POLLING_AND_MASTER_RETENTION[0], pib_value))
                else:
                    raise EnvironError("Unexpected value detected for pib parameter {0}: {1}".format(
                        self.POLLING_AND_MASTER_RETENTION[0], pib_value))
            except Exception as e:
                self.add_error_as_exception(e)

            self.sleep()
