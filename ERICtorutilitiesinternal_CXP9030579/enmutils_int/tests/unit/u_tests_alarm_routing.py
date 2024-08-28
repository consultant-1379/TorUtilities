#!/usr/bin/env python
import unittest2
from testslib import unit_test_utils
from mock import patch, Mock
from enmutils_int.lib.alarm_routing import AlarmRoutePolicy, AlarmRouteExistsError, ScriptEngineResponseValidationError


class AlarmRoutePolicyTestsInit(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.name = "FM_Setup_workload_policy"
        self.alarm_route_policy = AlarmRoutePolicy(self.user, self.name, [])

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_init__has_no_nodes(self):
        self.alarm_route_policy = AlarmRoutePolicy(self.user, self.name, nodes=None)
        self.assertTrue(self.alarm_route_policy.nodes is None)


class AlarmRoutePolicyTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.name = "FM_Setup_workload_policy"
        node = Mock()
        node.node_id = "LTE01"
        self.alarm_route_policy = AlarmRoutePolicy(self.user, self.name, [node])

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_init__has_nodes(self):
        self.alarm_route_policy = AlarmRoutePolicy(self.user, self.name, nodes=[Mock(), Mock()])
        self.assertTrue(self.alarm_route_policy.nodes >= 1)

    @patch("enmutils_int.lib.alarm_routing.AlarmRoutePolicy.disable")
    @patch("enmutils_int.lib.alarm_routing.AlarmRoutePolicy.delete", side_effect=Exception)
    @patch("enmutils_int.lib.alarm_routing.log.logger.debug")
    def test_teardown__execpt_log_called(self, mock_log, *_):
        self.alarm_route_policy._teardown()
        self.assertTrue(mock_log.called)

    @patch("enmutils_int.lib.alarm_routing.log.logger.debug")
    def test_create_route_is_successful_for_given_nodes(self, mock_logger_debug):
        response = Mock()
        output = [u'', u'Route FM_Setup_workload_policy created successfully']
        response.get_output.return_value = output
        self.user.enm_execute.return_value = response
        self.alarm_route_policy.create()
        self.assertTrue(mock_logger_debug.called)

    @patch("enmutils_int.lib.alarm_routing.log.logger.debug")
    def test_create_route_is_successful_for_entire_network(self, mock_logger_debug):
        self.alarm_route_policy.nodes = []
        response = Mock()
        output = [u'', u'Route FM_Setup_workload_policy created successfully']
        response.get_output.return_value = output
        self.user.enm_execute.return_value = response
        self.alarm_route_policy.create()
        self.assertTrue(mock_logger_debug.called)

    @patch("enmutils_int.lib.alarm_routing.log.logger.debug")
    def test_create_route_raises_alarm_route_exists_error(self, mock_logger_debug):
        response = Mock()
        output = [u'', u'The given route name already exists.']
        response.get_output.return_value = output
        self.user.enm_execute.return_value = response
        self.assertRaises(AlarmRouteExistsError, self.alarm_route_policy.create)
        self.assertFalse(mock_logger_debug.called)

    @patch("enmutils_int.lib.alarm_routing.log.logger.debug")
    def test_create_route_raises_script_engine_response_validation_error(self, mock_logger_debug):
        response = Mock()
        output = [u'', u'Failed to create the route']
        response.get_output.return_value = output
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, self.alarm_route_policy.create)
        self.assertFalse(mock_logger_debug.called)

    @patch("enmutils_int.lib.alarm_routing.log.logger.debug")
    def test_enable_route_is_successful(self, mock_logger_debug):
        response = Mock()
        output = [u'', u'Route FM_Setup_workload_policy updated successfully']
        response.get_output.return_value = output
        self.user.enm_execute.return_value = response
        self.alarm_route_policy.enable()
        self.assertTrue(mock_logger_debug.called)

    @patch("enmutils_int.lib.alarm_routing.log.logger.debug")
    def test_enable_route_raises_script_engine_response_validation_error(self, mock_logger_debug):
        response = Mock()
        output = [u'', u'Failed to update the route']
        response.get_output.return_value = output
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, self.alarm_route_policy.enable)
        self.assertFalse(mock_logger_debug.called)

    @patch("enmutils_int.lib.alarm_routing.log.logger.debug")
    def test_disable_route_is_successful(self, mock_logger_debug):
        response = Mock()
        output = [u'', u'Route FM_Setup_workload_policy updated successfully']
        response.get_output.return_value = output
        self.user.enm_execute.return_value = response
        self.alarm_route_policy.disable()
        self.assertTrue(mock_logger_debug.called)

    @patch("enmutils_int.lib.alarm_routing.log.logger.debug")
    def test_disable_route_raises_script_engine_response_validation_error(self, mock_logger_debug):
        response = Mock()
        output = [u'', u'Failed to update the route']
        response.get_output.return_value = output
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, self.alarm_route_policy.disable)
        self.assertFalse(mock_logger_debug.called)

    @patch("enmutils_int.lib.alarm_routing.log.logger.info")
    @patch("enmutils_int.lib.alarm_routing.log.logger.debug")
    def test_disable_route_does_not_fail_if_route_already_disabled(self, mock_logger_debug, mock_logger_info):
        response = Mock()
        output = [u'', u'Route FM_Setup_workload_policy Already in Deactive state, Cannot update route.']
        response.get_output.return_value = output
        self.user.enm_execute.return_value = response
        self.alarm_route_policy.disable()
        self.assertTrue(mock_logger_info.called)
        self.assertFalse(mock_logger_debug.called)

    @patch("enmutils_int.lib.alarm_routing.log.logger.debug")
    def test_delete_route_is_successful(self, mock_logger_debug):
        response = Mock()
        output = [u'', u' Route [FM_Setup_workload_policy] deleted successfully ']
        response.get_output.return_value = output
        self.user.enm_execute.return_value = response
        self.alarm_route_policy.delete()
        self.assertTrue(mock_logger_debug.called)

    @patch("enmutils_int.lib.alarm_routing.log.logger.debug")
    def test_delete_route_raises_script_engine_response_validation_error(self, mock_logger_debug):
        response = Mock()
        output = [u'', u'Failed to delete the route']
        response.get_output.return_value = output
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, self.alarm_route_policy.delete)
        self.assertFalse(mock_logger_debug.called)

    @patch("enmutils_int.lib.alarm_routing.log.logger.debug")
    def test_teardown(self, mock_logger_debug):
        disable_response = Mock()
        disable_output = [u'', u'Route FM_Setup_workload_policy updated successfully']
        disable_response.get_output.return_value = disable_output
        delete_response = Mock()
        delete_output = [u'', u' Route [FM_Setup_workload_policy] deleted successfully ']
        delete_response.get_output.return_value = delete_output
        self.user.enm_execute.side_effect = [disable_response, delete_response]
        self.alarm_route_policy._teardown()
        self.assertTrue(mock_logger_debug.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
