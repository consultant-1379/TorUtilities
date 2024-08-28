#!/usr/bin/env python
import unittest2
from mock import Mock
from testslib import unit_test_utils
from enmutils_int.lib.fm_active_alarms import FmActiveAlarmCheck


class FMactiveAlarmsCountTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        user = Mock()
        self.fm_active_alarms = FmActiveAlarmCheck(user)

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_check_active_alarms(self):
        response = Mock()
        response.get_output.return_value = ["OpenAlarm 20 instance(s) found"]
        self.fm_active_alarms.user.enm_execute.return_value = response
        total_alarms = self.fm_active_alarms.check_active_alarms()
        self.assertEqual(total_alarms, 60)

    def test_check_active_alarms__empty_response(self):
        response = Mock()
        response.get_output.return_value = [""]
        self.fm_active_alarms.user.enm_execute.return_value = response
        total_alarms = self.fm_active_alarms.check_active_alarms()
        self.assertEqual(total_alarms, 0)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
