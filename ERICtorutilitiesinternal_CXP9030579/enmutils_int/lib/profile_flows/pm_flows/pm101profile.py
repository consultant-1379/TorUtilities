import time
from functools import partial
from enmutils.lib import log
from enmutils.lib.exceptions import EnvironError
from enmutils.lib.persistence import picklable_boundmethod
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.services.deploymentinfomanager_adaptor import update_pib_parameter_on_enm, get_pib_value_on_enm


class Pm101Profile(GenericFlow):

    def __init__(self):
        """
        Init Method
        """
        super(Pm101Profile, self).__init__()
        self.PMICCELLTRACEFILERETENTIONPERIODINMINUTES = 0
        self.PMICEBMFILERETENTIONPERIODINMINUTES = 0
        self.RETENTION_VALUES_SLEEP_TIME = None

    def execute_flow(self):
        """
        Main flow for PM_101
        """

        self.state = "RUNNING"
        self.RETENTION_VALUES_SLEEP_TIME = zip(self.CELLTRACE_AND_EBM_RETENTION['pmicEbmFileRetentionPeriodInMinutes'],
                                               self.CELLTRACE_AND_EBM_RETENTION['pmicCelltraceFileRetentionPeriodInMinutes'], [4, 0.5, 0.5])
        self._sleep_until()
        while self.keep_running():
            try:
                self.perform_pib_operations()
            except Exception as e:
                raise EnvironError("Failed to update PIB parameters, occurred {0} error".format(e))
            self.sleep_until_time()

    def update_pib_parameter(self, celltrace_retention=180, ebm_retention=180):
        """
        Updates PIB parameter on ENM

        :param celltrace_retention: Name of PIB Parameter
        :type celltrace_retention: int
        :param ebm_retention: Name of PIB Parameter
        :type ebm_retention: int
        """
        try:
            update_pib_parameter_on_enm(enm_service_name="flsserv",
                                        pib_parameter_name="pmicCelltraceFileRetentionPeriodInMinutes",
                                        pib_parameter_value=str(celltrace_retention))
            log.logger.debug(
                "PIB parameter pmicCelltraceFileRetentionPeriodInMinutes is updated to {0}".format(celltrace_retention))
            update_pib_parameter_on_enm(enm_service_name="flsserv",
                                        pib_parameter_name="pmicEbmFileRetentionPeriodInMinutes",
                                        pib_parameter_value=str(ebm_retention))
            log.logger.debug(
                "PIB parameter pmicEbmFileRetentionPeriodInMinutes is updated to {0}".format(ebm_retention))
        except Exception as e:
            self.add_error_as_exception(e)

    def perform_pib_operations(self):
        """
        Updates PIB configuration parameter values on all the pm services in the system
        """
        self.PMICCELLTRACEFILERETENTIONPERIODINMINUTES = get_pib_value_on_enm(enm_service_name="flsserv",
                                                                              pib_parameter_name="pmicCelltraceFileRetentionPeriodInMinutes")
        self.PMICEBMFILERETENTIONPERIODINMINUTES = get_pib_value_on_enm(enm_service_name="flsserv",
                                                                        pib_parameter_name="pmicEbmFileRetentionPeriodInMinutes")
        self.teardown_list.append(partial(picklable_boundmethod(self.update_pib_parameter),
                                          self.PMICCELLTRACEFILERETENTIONPERIODINMINUTES,
                                          self.PMICEBMFILERETENTIONPERIODINMINUTES))
        for ebm_retention, celltrace_retention, sleep_time in self.RETENTION_VALUES_SLEEP_TIME:
            self.update_pib_parameter(celltrace_retention, ebm_retention)
            log.logger.debug("Sleeping for {0} hours, after updating the 'pmicCelltraceFileRetentionPeriodInMinutes', "
                             "'pmicEbmFileRetentionPeriodInMinutes' pib parameter's values in ENM".format(sleep_time))
            self.check_profile_memory_usage()
            self.state = "SLEEPING"
            time.sleep(60 * 60 * sleep_time)
            self.state = "RUNNING"
        self.update_pib_parameter(self.PMICCELLTRACEFILERETENTIONPERIODINMINUTES,
                                  self.PMICEBMFILERETENTIONPERIODINMINUTES)
