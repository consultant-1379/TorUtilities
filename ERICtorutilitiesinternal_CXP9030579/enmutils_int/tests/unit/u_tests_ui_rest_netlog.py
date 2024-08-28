#!/usr/bin/env python
import unittest2
from mock import patch, Mock

from enmutils.lib.exceptions import ScriptEngineResponseValidationError
from enmutils_int.lib import fm
from testslib import unit_test_utils


class NetlogUIRestCase(unittest2.TestCase):

    def setUp(self):
        self.mock_user = Mock
        self.erbs_node1 = Mock(
            node_id="netsim_LTE01ERBS00100", node_ip="ip", mim_version="5.1.120", model_identity="1094-174-285",
            security_state='ON', normal_user='test', normal_password='test', secure_user='test',
            secure_password='test', subnetwork='SubNetwork=ERBS-SUBNW-1', netsim="netsimlin704", simulation="LTE01",
            user=self.mock_user)
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.fm.time.sleep", return_value=0)
    @patch("enmutils_int.lib.fm.Request.execute")
    def test_collect_erbs_network_logs(self, mock_execute, _):
        response_log = "upload on log type ALARM_LOG successfully started"
        mock_response = Mock()
        mock_response.get_output.return_value = [
            ">>netlog upload ieatnetsimv6018-07_LTE26ERBS00032 ALARM_LOG",
            "FDN: NetworkElement=ieatnetsimv6018-07_LTE26ERBS00032",
            "upload on log type ALARM_LOG successfully started"]

        mock_execute.return_value = mock_response

        expected_result = (fm.collect_erbs_network_logs(self.mock_user, self.erbs_node1)[1])
        self.assertEqual(expected_result, response_log)

    @patch("enmutils_int.lib.fm.time.sleep", return_value=0)
    @patch("enmutils_int.lib.fm.Request.execute")
    def test_collect_erbs_network_logs_raises_exception_if_no_output_returned(self, mock_execute, _):
        output = ["", ""]
        mock_response = Mock()
        mock_response.get_output.return_value = output
        mock_execute.return_value = mock_response

        self.assertRaises((ScriptEngineResponseValidationError, fm.collect_erbs_network_logs, self.mock_user,
                           self.erbs_node1)[1])

    @patch("enmutils_int.lib.fm.Request.execute")
    def test_collect_enodeb_network_logs(self, mock_execute):
        response_log = "upload on log type AlarmLog successfully started"
        mock_response = Mock()
        mock_response.get_output.return_value = [
            ">>netlog upload LTE45dg2ERBS0160 AlarmLog",
            "FDN: NetworkElement=LTE45dg2ERBS0160",
            "upload on log type AlarmLog successfully started"]

        mock_execute.return_value = mock_response

        expected_result = (fm.collect_eNodeB_network_logs(self.mock_user, self.erbs_node1)[1])
        self.assertEqual(expected_result, response_log)

    @patch("enmutils_int.lib.fm.Request.execute")
    def test_collect_enodeb_network_logs_raises_exception_if_no_output_returned(self, mock_execute):
        output = ["", ""]
        mock_response = Mock()
        mock_response.get_output.return_value = output
        mock_execute.return_value = mock_response

        self.assertRaises(
            (ScriptEngineResponseValidationError, fm.collect_eNodeB_network_logs, self.mock_user, self.erbs_node1)[1])

    @patch("enmutils_int.lib.fm.time.sleep", return_value=0)
    @patch("enmutils_int.lib.fm.Request.execute")
    def test_collect_sgsn_network_logs(self, mock_execute, _):
        response_log = "upload on log type mmi successfully started"
        mock_response = Mock()
        mock_response.get_output.return_value = [
            ">>netlog upload SGSN-16A-CP01-V155 mmi;fm_alarm;fm_event;NodeDump",
            "FDN: NetworkElement=SGSN-16A-CP01-V155",
            "upload on log type mmi successfully started"]

        mock_execute.return_value = mock_response

        expected_result = (fm.collect_sgsn_network_logs(self.mock_user, self.erbs_node1)[1])
        self.assertEqual(expected_result, response_log)

    @patch("enmutils_int.lib.fm.time.sleep", return_value=0)
    @patch("enmutils_int.lib.fm.Request.execute")
    def test_collect_sgsn_network_logs_raises_exception_if_no_output_returned(self, mock_execute, _):
        output = ["", ""]
        mock_response = Mock()
        mock_response.get_output.return_value = output
        mock_execute.return_value = mock_response

        self.assertRaises(
            (ScriptEngineResponseValidationError, fm.collect_sgsn_network_logs, self.mock_user, self.erbs_node1)[1])

    @patch("enmutils_int.lib.fm.time.sleep", return_value=0)
    @patch("enmutils_int.lib.fm.Request.execute")
    def test_collect_mgw_network_logs(self, mock_execute, _):
        response_log = "upload on log type SYSTEM_LOG successfully started"
        mock_response = Mock()
        mock_response.get_output.return_value = [
            ">>netlog upload ieatnetsimv6023-23_K3C120150 SYSTEM_LOG",
            "FDN: NetworkElement=ieatnetsimv6023-23_K3C120150",
            "upload on log type SYSTEM_LOG successfully started"]

        mock_execute.return_value = mock_response

        expected_result = (fm.collect_mgw_network_logs(self.mock_user, self.erbs_node1)[1])
        self.assertEqual(expected_result, response_log)

    @patch("enmutils_int.lib.fm.time.sleep", return_value=0)
    @patch("enmutils_int.lib.fm.Request.execute")
    def test_collect_mgw_network_logs_raises_exception_if_no_output_returned(self, mock_execute, _):
        output = ["", ""]
        mock_response = Mock()
        mock_response.get_output.return_value = output
        mock_execute.return_value = mock_response

        self.assertRaises(
            (ScriptEngineResponseValidationError, fm.collect_mgw_network_logs, self.mock_user, self.erbs_node1)[1])


if __name__ == '__main__':
    unittest2.main(verbosity=2)
