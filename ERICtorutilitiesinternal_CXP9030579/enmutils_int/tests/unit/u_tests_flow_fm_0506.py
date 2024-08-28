#!/usr/bin/env python
import unittest2
from enmutils.lib.enm_node import ERBSNode
from enmutils.lib.exceptions import FailedNetsimOperation, AlarmRouteExistsError, ScriptEngineResponseValidationError
from enmutils_int.lib.alarm_routing import AlarmRoutePolicy
from enmutils_int.lib.netsim_operations import NetsimOperation
from enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow import Fm0506
from mock import patch, Mock, PropertyMock
from testslib import unit_test_utils


class FM0506UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Fm0506()
        self.nodes = [
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00001', unit_test_utils.generate_configurable_ip(), 'F.1.101',
                     '5783-904-386', '', 'netsim', 'netsim', 'netsim', 'netsim', primary_type='ERBS'),
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00002', unit_test_utils.generate_configurable_ip(), 'F.1.101',
                     '5783-904-386', '', 'netsim', 'netsim', 'netsim', 'netsim', primary_type='ERBS'),
            ERBSNode('ieatnetsimv5051-01_LTE01ERBS00003', unit_test_utils.generate_configurable_ip(), 'F.1.101',
                     '5783-904-386', '', 'netsim', 'netsim', 'netsim', 'netsim', primary_type='ERBS')
        ]
        self.user = Mock()
        self.flow.USER_ROLES = ["FM_Administrator"]
        self.flow.NUM_USERS = 1
        self.flow.SETUP_STEPS = {"CEASE_ALARM": True, "AUTO_ACK": True, "DELAYED_ACK": True}
        self.flow.NETSIMS = ["ERBS1"]
        self.flow.teardown_list = []
        self.error_response = [AlarmRouteExistsError, ScriptEngineResponseValidationError("Exception", self.nodes)]
        self.delay_in_hours = '24'
        self.delayed_ack_check_interval_minutes = 10
        self.service_locations = self.service_ips = [unit_test_utils.generate_configurable_ip()]

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.create_users")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.delayed_ack")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.auto_ack")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.cease_alarms")
    def test_execute_fm0506_normal_flow__adds_exception(self, mock_cease_alarms, mock_auto_ack, mock_delayed_ack,
                                                        mock_add_error_as_exception, *_):
        mock_auto_ack.side_effect = Exception
        self.flow.execute_fm_0506_normal_flow()
        self.assertTrue(mock_add_error_as_exception.called)
        self.assertTrue(mock_cease_alarms.called)
        self.assertTrue(mock_auto_ack.called)
        self.assertTrue(mock_delayed_ack.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.create_users")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.delayed_ack")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.auto_ack")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.cease_alarms")
    def test_execute_fm0506_normal_flow__all_true(self, mock_cease_alarms, mock_auto_ack, mock_delayed_ack, *_):
        self.flow.execute_fm_0506_normal_flow()
        self.assertTrue(mock_cease_alarms.called)
        self.assertTrue(mock_auto_ack.called)
        self.assertTrue(mock_delayed_ack.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.create_users")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.delayed_ack")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.auto_ack")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.cease_alarms")
    def test_execute_fm0506_normal_flow__all_false(self, mock_cease_alarms, mock_auto_ack, mock_delayed_ack, *_):
        self.flow.SETUP_STEPS = {"CEASE_ALARM": False, "AUTO_ACK": False, "DELAYED_ACK": False}
        self.flow.execute_fm_0506_normal_flow()
        self.assertFalse(mock_cease_alarms.called)
        self.assertFalse(mock_auto_ack.called)
        self.assertFalse(mock_delayed_ack.called)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.log.logger.debug')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.NetsimOperation.execute_command_string")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.NetsimOperation")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.log.logger.info')
    def test_cease_alarms__success(self, mock_logger_info, mock_netsims, mock_execute_command_string, mock_logger_debug):
        mock_netsims.return_value.mock_execute_command_string.return_value = self.nodes
        response = Mock()
        mock_execute_command_string.return_value = response
        self.flow.cease_alarms(self.nodes)
        self.assertTrue(mock_logger_info.called)
        self.assertTrue(mock_logger_debug.called)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.add_error_as_exception')
    @patch("enmutils_int.lib.netsim_operations.NetsimOperation.execute_command_string")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.NetsimOperation")
    def test_cease_alarms__throws_failed_netsim_operation_exception(self, mock_netsims, mock_execute_command_string,
                                                                    mock_add_error_as_exception):
        mock_netsims.return_value = NetsimOperation(self.nodes)
        mock_execute_command_string.side_effect = FailedNetsimOperation
        self.flow.cease_alarms(self.nodes)
        self.assertTrue(mock_execute_command_string.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.add_error_as_exception')
    @patch("enmutils_int.lib.netsim_operations.NetsimOperation.execute_command_string")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.NetsimOperation")
    def test_cease_alarms__adds_exception_as_error(self, mock_netsims, mock_execute_command_string,
                                                   mock_add_error_as_exception):
        mock_netsims.return_value = NetsimOperation(self.nodes)
        mock_execute_command_string.side_effect = Exception
        self.flow.cease_alarms(self.nodes)
        self.assertTrue(mock_execute_command_string.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.AlarmRoutePolicy")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.log.logger.info')
    def test_auto_ack__success(self, mock_logger_info, mock_create):
        mock_alarm_route_policy = Mock()
        mock_alarm_route_policy.return_value = AlarmRoutePolicy(self.user, "FM_Setup_workload_policy",
                                                                nodes=self.nodes[1:])
        mock_teardown_policy = Mock()
        mock_teardown_policy.return_value = mock_alarm_route_policy(self.user, "FM_Setup_workload_policy")
        self.flow.teardown_list.append(mock_teardown_policy)
        self.flow.auto_ack(self.user, self.nodes)
        self.assertTrue(mock_logger_info.called)
        self.assertTrue(mock_create.called)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.AlarmRoutePolicy.delete")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.AlarmRoutePolicy.disable")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.AlarmRoutePolicy.create")
    def test_auto_ack__throws_alarm_route_exists_error(self, mock_create, mock_disable, mock_delete, *_):
        mock_alarm_route_policy = Mock()
        mock_alarm_route_policy.return_value = None
        mock_create.side_effect = [self.error_response[0], " "]

        self.flow.auto_ack(self.user, self.nodes)
        self.assertTrue(mock_create.called)
        self.assertTrue(mock_disable.called)
        self.assertTrue(mock_delete.called)

    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.AlarmRoutePolicy.create")
    def test_auto_ack__throws_script_engine_response_validation_error(self, mock_create, mock_add_error_as_exception):
        mock_alarm_route_policy = Mock()
        mock_alarm_route_policy.return_value = None
        mock_create.side_effect = self.error_response[1]

        self.flow.auto_ack(self.user, self.nodes)
        self.assertTrue(mock_create.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.FmDelayedAck.enable_delayed_acknowledgement_on_enm")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.FmDelayedAck."
           "update_check_interval_for_delayed_acknowledge_on_enm")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.FmDelayedAck.update_the_delay_in_hours_on_enm")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.FmDelayedAck")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.log.logger.info')
    def test_delayed_ack__success(self, mock_logger_info, mock_fm_delayed_ack, *_):
        mock_fm_delayed_ack.update_the_delay_in_hours_on_enm.return_value = self.delay_in_hours
        mock_fm_delayed_ack.update_check_interval_for_delayed_acknowledge_on_enm.return_value = 10
        mock_fm_delayed_ack.enable_delayed_acknowledgement_on_enm.return_value = True
        self.flow.teardown_list.append(mock_fm_delayed_ack)
        self.flow.delayed_ack()
        self.assertTrue(mock_logger_info.called)
        self.assertTrue(mock_fm_delayed_ack.called)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.FmDelayedAck.enable_delayed_acknowledgement_on_enm")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.FmDelayedAck."
           "update_check_interval_for_delayed_acknowledge_on_enm")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.FmDelayedAck.update_the_delay_in_hours_on_enm")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.FmDelayedAck")
    @patch('enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.log.logger.info')
    def test_delayed_ack__adds_error_as_exception(self, mock_logger_info, mock_fm_delayed_ack,
                                                  mock_add_error_as_exception, *_):
        mock_fm_delayed_ack.return_value.update_the_delay_in_hours_on_enm.side_effect = Exception
        self.flow.teardown_list.append(mock_fm_delayed_ack)
        self.flow.delayed_ack()
        self.assertTrue(mock_logger_info.called)
        self.assertTrue(mock_add_error_as_exception.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
