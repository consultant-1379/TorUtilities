#!/usr/bin/env python
import unittest2
from mock import patch, Mock

from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_common_utils import (toggle_pib_historical_cm_export,
                                                                                 confirm_eniq_topology_export_enabled)
from testslib import unit_test_utils


class CmExportCommonUtilsUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_common_utils.config.is_a_cloud_deployment',
           return_value=False)
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_common_utils.shell.run_cmd_on_emp_or_ms")
    @patch("enmutils.lib.log.logger.debug")
    def test_confirm_eniq_topology_export_enabled__returns_true(self, mock_debug, mock_run_cmd_on_emp_or_ms, _):
        mock_run_cmd_on_emp_or_ms.return_value = Mock(rc=0, stdout="ENIQ Daily Topology export is currently enabled")
        is_eniq_enabled = confirm_eniq_topology_export_enabled()
        self.assertEqual(True, is_eniq_enabled)
        self.assertEqual(2, mock_debug.call_count)
        mock_debug.assert_called_with("ENIQ daily topology export, enabled on ENM.")
        mock_run_cmd_on_emp_or_ms.assert_called_with(
            cmd='/usr/bin/python /opt/ericsson/ENM_ENIQ_Integration/eniq_enm_integration.py showExportTimes',
            get_pty=True, timeout=120)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_common_utils.config.is_a_cloud_deployment',
           return_value=True)
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_common_utils.shell.run_cmd_on_emp_or_ms")
    @patch("enmutils.lib.log.logger.debug")
    def test_confirm_eniq_topology_export_enabled__returns_false(self, mock_debug, mock_run_cmd_on_emp_or_ms, _):
        mock_run_cmd_on_emp_or_ms.return_value = Mock(rc=1)
        is_eniq_enabled = confirm_eniq_topology_export_enabled()
        self.assertEqual(False, is_eniq_enabled)
        self.assertEqual(2, mock_debug.call_count)
        mock_debug.assert_called_with("ENIQ daily topology export, is not enabled on ENM.")
        mock_run_cmd_on_emp_or_ms.assert_called_with(
            cmd='sudo /usr/bin/python /opt/ericsson/ENM_ENIQ_Integration/eniq_venm_integration.py showExportTimes',
            get_pty=True, timeout=120)

    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_common_utils.toggle_pib_historicalcmexport")
    @patch("enmutils_int.lib.profile_flows.cmexport_flows.cmexport_common_utils.log.logger.debug")
    def test_toggle_pib_historical_cm_export__is_successful(self, mock_debug, mock_toggle_pib_historicalcmexport):
        toggle_pib_historical_cm_export()
        self.assertEqual(2, mock_debug.call_count)
        mock_toggle_pib_historicalcmexport.assert_callled_with("true")


if __name__ == "__main__":
    unittest2.main(verbosity=2)
