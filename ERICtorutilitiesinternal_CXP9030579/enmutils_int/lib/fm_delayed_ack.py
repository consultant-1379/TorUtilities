# ********************************************************************
# Name    : FM Delayed Acknowledgement
# Summary : Module for setting FM delayed Acknowledgement values.
#           Allows the user to set PIB FM values to enable, disable,
#           update or reset the FM delayed acknowledgement policy.
# ********************************************************************


from enmutils.lib import log
from enmutils_int.lib.services.deploymentinfomanager_adaptor import update_pib_parameter_on_enm


class FmDelayedAck(object):

    DELAY_IN_HOURS = 24
    DELAYED_ACK_CHECK_INTERVAL_IN_MINUTES = 10

    def __init__(self, vm_addresses=None, delay_in_hours=DELAY_IN_HOURS, delayed_ack_check_interval_minutes=DELAYED_ACK_CHECK_INTERVAL_IN_MINUTES):
        """
        FmDelayedAck Constructor
        :type vm_addresses: list[strings]
        :param vm_addresses: Addresses of VMs in the deployment which have pib deployed (ip or resolvable hostname)
        :type delay_in_hours: int
        :param delay_in_hours: Number of hours after which a new alarm will get acknowledged
        :type delayed_ack_check_interval_minutes: int
        :param delayed_ack_check_interval_minutes: Length of the interval, in minutes, between checks for alarms that are older than 'time_after_which_to_ack_alarms'
        """
        self.delay_in_hours = delay_in_hours
        self.delayed_ack_check_interval_minutes = delayed_ack_check_interval_minutes
        self.service = "fmserv"

    def enable_delayed_acknowledgement_on_enm(self):
        """
        Enables delayed acknowledgement for alarms in ENM
        """
        update_pib_parameter_on_enm(self.service, "FMA_DELAYED_ACK_OF_ALARMS_ON", "true")
        log.logger.debug("Successfully set Delayed Acknowledgement to true on this deployment")

    def disable_delayed_acknowledgement_on_enm(self):
        """
        Disables delayed acknowledgement for alarms in ENM
        """
        update_pib_parameter_on_enm(self.service, "FMA_DELAYED_ACK_OF_ALARMS_ON", "false")
        log.logger.debug("Successfully set Delayed Acknowledgement to false on this deployment")

    def update_check_interval_for_delayed_acknowledge_on_enm(self):
        """
        Updates the interval, in minutes, between checks for alarms to be acknowledged
        """
        update_pib_parameter_on_enm(self.service, "FMA_DELAYED_ACK_CHECK_INTERVAL",
                                    str(self.delayed_ack_check_interval_minutes))
        log.logger.debug("Successfully updated the interval for checking alarms to {0} minutes on this "
                         "deployment".format(self.delayed_ack_check_interval_minutes))

    def update_the_delay_in_hours_on_enm(self):
        """
        Updates number of hours for acknowledgment delay
        """
        update_pib_parameter_on_enm(self.service, "FMA_TIME_TO_DELAYED_ACK_ALARMS",
                                    str(self.delay_in_hours))
        log.logger.debug("Successfully updated the acknowledgment delay to {0} hours on this deployment"
                         .format(self.delay_in_hours))

    def reset_delay_to_default_value_on_enm(self):
        """
        Sets the instance delay_in_hours value back to the value of class variable  DELAY_IN_HOURS
        """
        self.delay_in_hours = FmDelayedAck.DELAY_IN_HOURS
        self.update_the_delay_in_hours_on_enm()

    def reset_delayed_ack_check_interval_to_default_value_on_enm(self):
        """
        Sets the instance delayed_ack_check_interval_minutes back to value of class variable DELAYED_ACK_CHECK_INTERVAL_IN_MINUTES
        """
        self.delayed_ack_check_interval_minutes = FmDelayedAck.DELAYED_ACK_CHECK_INTERVAL_IN_MINUTES
        self.update_check_interval_for_delayed_acknowledge_on_enm()

    def _teardown(self):
        """
        Secret teardown method for Workload
        """
        try:
            self.disable_delayed_acknowledgement_on_enm()
        except Exception as e:
            log.logger.debug(str(e))
