#!/usr/bin/env python
import unittest2

from mock import patch
from testslib import unit_test_utils
from enmutils_int.lib.workload import (fm_01, fm_02, fm_03, fm_0506, fm_08, fm_09, fm_10, fm_11, fm_12,
                                       fm_14, fm_15, fm_17, fm_20, fm_21, fm_25, fm_26, fm_27, fm_31, fm_32)


class FmProfileModulesExecuteFlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_01_flow.Fm01.execute_fm_01_alarm_rate_normal_flow")
    def test_run_in_fm_01__is_successful(self, mock_execute_flow):
        fm_01.FM_01().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_02_flow.Fm02.execute_fm_02_alarm_rate_normal_flow")
    def test_run_in_fm_02__is_successful(self, mock_execute_flow):
        fm_02.FM_02().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_03_flow.Fm03.execute_fm_03_alarm_rate_normal_flow")
    def test_run_in_fm_03__is_successful(self, mock_execute_flow):
        fm_03.FM_03().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_0506_flow.Fm0506.execute_fm_0506_normal_flow")
    def test_run_in_fm_0506__is_successful(self, mock_execute_flow):
        fm_0506.FM_0506().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_08_flow.Fm08.execute_flow_fm_08")
    def test_run_in_fm_08__is_successful(self, mock_execute_flow):
        fm_08.FM_08().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_09_flow.Fm09.execute_flow_fm_09")
    def test_run_in_fm_09__is_successful(self, mock_execute_flow):
        fm_09.FM_09().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_10_flow.Fm10.execute_flow_fm_10")
    def test_run_in_fm_10__is_successful(self, mock_execute_flow):
        fm_10.FM_10().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_11_flow.Fm11.execute_flow_fm_11")
    def test_run_in_fm_11__is_successful(self, mock_execute_flow):
        fm_11.FM_11().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_12_flow.Fm12.execute_flow")
    def test_run_in_fm_12__is_successful(self, mock_execute_flow):
        fm_12.FM_12().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow.FmAlarmHistorySearchFlow."
           "execute_flow_fm_alarm_history_search")
    def test_run_in_fm_14__is_successful(self, mock_execute_flow):
        fm_14.FM_14().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow.FmAlarmHistorySearchFlow."
           "execute_flow_fm_alarm_history_search")
    def test_run_in_fm_15__is_successful(self, mock_execute_flow):
        fm_15.FM_15().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_alarm_history_search_flow.FmAlarmHistorySearchFlow."
           "execute_flow_fm_alarm_history_search")
    def test_run_in_fm_17__is_successful(self, mock_execute_flow):
        fm_17.FM_17().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_20_flow.Fm20.execute_flow_fm_20")
    def test_run_in_fm_20__is_successful(self, mock_execute_flow):
        fm_20.FM_20().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_21_flow.Fm21.execute_flow_fm_21")
    def test_run_in_fm_21__is_successful(self, mock_execute_flow):
        fm_21.FM_21().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_25_flow.Fm25.execute_flow_fm_25")
    def test_run_in_fm_25__is_successful(self, mock_execute_flow):
        fm_25.FM_25().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_26_flow.Fm26.alarm_history_cli_capability_main_flow")
    def test_run_in_fm_26__is_successful(self, mock_execute_flow):
        fm_26.FM_26().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_27_flow.Fm27.execute_flow")
    def test_run_in_fm_27__is_successful(self, mock_execute_flow):
        fm_27.FM_27().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_31_flow.Fm31.execute_flow")
    def test_run_in_fm_31__is_successful(self, mock_execute_flow):
        fm_31.FM_31().run()
        self.assertEqual(mock_execute_flow.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_32_flow.Fm32.execute_fm_32_alarm_flow")
    def test_run_in_fm_32__is_successful(self, mock_execute_flow):
        fm_32.FM_32().run()
        self.assertEqual(mock_execute_flow.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
