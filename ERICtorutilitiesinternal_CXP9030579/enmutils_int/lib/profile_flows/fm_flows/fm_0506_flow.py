from enmutils.lib import log
from enmutils.lib.exceptions import (FailedNetsimOperation, AlarmRouteExistsError, ScriptEngineResponseValidationError,
                                     EnmApplicationError)
from enmutils_int.lib.alarm_routing import AlarmRoutePolicy
from enmutils_int.lib.fm_delayed_ack import FmDelayedAck
from enmutils_int.lib.netsim_operations import NetsimOperation
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from retrying import retry


class Fm0506(GenericFlow):

    NETSIMS = []
    PERCENTAGE_NODES_ASSIGNED_TO_POLICY = 50
    DELAYED_ACKNOWLEDGE_HRS = 24   # Update value changes in enmutils_int/lib/nrm_default_configurations/apt_values.py FM_DATA variable

    def execute_fm_0506_normal_flow(self):
        """
        This function executes the main flow for FM_0506
        """
        user = self.create_users(self.NUM_USERS, self.USER_ROLES, fail_fast=False, safe_request=True, retry=True)[0]
        nodes = self.get_nodes_list_by_attribute(node_attributes=["node_id", "netsim", "simulation",
                                                                  "primary_type", "node_name"])
        self.state = "RUNNING"
        if self.SETUP_STEPS["CEASE_ALARM"]:
            self.cease_alarms(nodes)
            log.logger.debug("Cease alarms completed")
        if self.SETUP_STEPS["AUTO_ACK"]:
            try:
                self.auto_ack(user, nodes)
                log.logger.debug("Auto ack setup completed")
            except Exception as e:
                self.add_error_as_exception(EnmApplicationError(e))
        if self.SETUP_STEPS["DELAYED_ACK"]:
            self.delayed_ack()
            log.logger.debug("Delayed ack setup completed")

    def cease_alarms(self, nodes):
        """
        Cease all alarms
        :param nodes: List of node objects
        :type nodes: list
        """
        log.logger.info('Cease all alarms')
        netsim_operation = NetsimOperation(nodes)
        try:
            netsim_operation.execute_command_string('ceasealarm:all;')
            log.logger.debug("All alarms stopped.")
        except FailedNetsimOperation as e:
            self.add_error_as_exception(e)
        except Exception as e:
            self.add_error_as_exception(e)

    @retry(retry_on_exception=lambda e: isinstance(e, AlarmRouteExistsError), stop_max_attempt_number=2)
    def auto_ack(self, user, nodes):
        """
        Auto acknowledge alarms
        :param user: ENM user
        :type user: enmutils.lib.enm_user_2.User
        :param nodes: List of node objects
        :type nodes: list
        :raises AlarmRouteExistsError:  if number of retries are completed and still the alarm route exists
        """
        log.logger.info('Set auto_ack')
        total_nodes = len(nodes)
        number_nodes_for_auto_ack = int(total_nodes / (100.0 / self.PERCENTAGE_NODES_ASSIGNED_TO_POLICY))
        policy = AlarmRoutePolicy(user, "FM_Setup_workload_policy", nodes=nodes[number_nodes_for_auto_ack:])
        try:
            policy.create()
            teardown_policy = AlarmRoutePolicy(user, policy.name)
            self.teardown_list.append(teardown_policy)
        except AlarmRouteExistsError:
            log.logger.info("Alarm route already exists! Trying to disable and delete the alarm route")
            policy.disable()
            policy.delete()
            raise
        except ScriptEngineResponseValidationError as e:
            self.add_error_as_exception(e)

    def delayed_ack(self):
        """
        Delay the acknowledgement
        """
        log.logger.info('Delayed Acknowledge')
        fm_delayed_ack = FmDelayedAck(delay_in_hours='{0}'.format(self.DELAYED_ACKNOWLEDGE_HRS),
                                      delayed_ack_check_interval_minutes=10)
        try:
            fm_delayed_ack.update_the_delay_in_hours_on_enm()
            fm_delayed_ack.update_check_interval_for_delayed_acknowledge_on_enm()
            fm_delayed_ack.enable_delayed_acknowledgement_on_enm()
            self.teardown_list.append(fm_delayed_ack)
        except Exception as e:
            self.add_error_as_exception(e)
