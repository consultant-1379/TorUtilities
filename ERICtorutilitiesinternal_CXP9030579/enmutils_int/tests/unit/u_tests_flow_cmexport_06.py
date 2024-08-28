#!/usr/bin/env python
import unittest2
from mock import patch, PropertyMock

from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow import CmExport19Flow
from testslib import unit_test_utils


class CmExport19FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = CmExport19Flow()
        self.flow.USER_ROLES = 'CM_REST_Administrator'
        self.flow.NUM_USERS = 1

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.confirm_eniq_topology_export_enabled',
           return_value=False)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.toggle_pib_historical_cm_export')
    def test_confirm_export_configured__adds_exception(self, mock_toggle_pib_historical_cm_export, mock_add_error, *_):
        self.flow.confirm_export_configured()
        self.assertEqual(0, mock_toggle_pib_historical_cm_export.call_count)
        self.assertEqual(1, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.confirm_eniq_topology_export_enabled',
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.toggle_pib_historical_cm_export')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.add_error_as_exception')
    def test_confirm_export_configured__success(self, mock_add_error, mock_toggle_pib_historical_cm_export, *_):
        self.flow.confirm_export_configured()
        self.assertEqual(1, mock_toggle_pib_historical_cm_export.call_count)
        self.assertEqual(0, mock_add_error.call_count)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.partial')
    def test_set_teardown_objects__success(self, mock_partial):
        self.flow.set_teardown_objects()
        self.assertEqual('false', mock_partial.call_args[0][1])

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.is_a_cloud_deployment', return_value=False)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.get_emp', return_value="emp")
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.get_ms_host', return_value="lms")
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.pexpect.spawn.expect', return_value=1)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.pexpect.spawn.sendline')
    def test_execute_setup_commands__success(self, mock_send, *_):
        self.flow.execute_setup_commands()
        self.assertEqual(4, mock_send.call_count)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.is_a_cloud_deployment', return_value=True)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.get_emp', return_value="emp")
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.get_ms_host', return_value="lms")
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.pexpect.spawn.expect', return_value=1)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.pexpect.spawn.sendline')
    def test_execute_setup_commands__cloud(self, mock_send, *_):
        self.flow.execute_setup_commands()
        self.assertEqual(4, mock_send.call_count)
        mock_send.assert_any_call("sudo /usr/bin/python /opt/ericsson/ENM_ENIQ_Integration/eniq_venm_integration.py "
                                  "eniqcmexport")

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.set_teardown_objects')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.is_enm_on_cloud_native')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.confirm_eniq_topology_export_enabled',
           return_value=False)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.is_eniq_server',
           return_value=(True, ['ip1', 'ip2']))
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.confirm_export_configured')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.execute_setup_commands')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.create_profile_users')
    def test_execute_flow__success(self, mock_execute, mock_confirm, *_):
        self.flow.execute_flow()
        self.assertEqual(1, mock_execute.call_count)
        self.assertEqual(0, mock_confirm.call_count)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.set_teardown_objects')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.confirm_eniq_topology_export_enabled',
           return_value=False)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.is_eniq_server',
           return_value=(True, ['ip1', 'ip2']))
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.confirm_export_configured')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.execute_setup_commands')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.create_profile_users')
    def test_execute_flow__success_for_non_cenm(self, mock_execute, mock_confirm, *_):
        self.flow.execute_flow()
        self.assertEqual(1, mock_execute.call_count)
        self.assertEqual(1, mock_confirm.call_count)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.set_teardown_objects')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.confirm_eniq_topology_export_enabled',
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.is_eniq_server',
           return_value=(True, ['ip1', 'ip2']))
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.confirm_export_configured')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.execute_setup_commands')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.create_profile_users')
    def test_execute_flow__already_enabled(self, mock_execute, mock_confirm, *_):
        self.flow.execute_flow()
        self.assertEqual(1, mock_execute.call_count)
        self.assertEqual(0, mock_confirm.call_count)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.set_teardown_objects')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.confirm_eniq_topology_export_enabled',
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.is_eniq_server',
           return_value=(False, ['ip1', 'ip2']))
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.confirm_export_configured')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.execute_setup_commands')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.create_profile_users')
    def test_execute_flow__eniq_not_configured(self, mock_execute, mock_confirm, *_):
        self.flow.execute_flow()
        self.assertEqual(1, mock_execute.call_count)
        self.assertEqual(0, mock_confirm.call_count)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.set_teardown_objects')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.state',
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.is_enm_on_cloud_native', return_value=False)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.confirm_eniq_topology_export_enabled',
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.confirm_export_configured',
           side_effect=Exception("Error"))
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.is_eniq_server',
           return_value=(True, ['ip1', 'ip2']))
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.execute_setup_commands')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_06_flow.CmExport19Flow.add_error_as_exception')
    def test_execute_flow__adds_exception(self, mock_add_error, *_):
        self.flow.execute_flow()
        self.assertEqual(1, mock_add_error.call_count)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
