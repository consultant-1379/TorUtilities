#!/usr/bin/env python
import unittest2

from enmutils.lib.exceptions import FailedNetsimOperation

from enmutils_int.lib.netsim_operations import AlarmBurst
from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import setup_verify, func_dec


class AlarmBurstAcceptanceTests(unittest2.TestCase):

    NUM_NODES = {'ERBS': 1}

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        # duration=600s to ensure that alarm bust is still running by the time it comes to shut down this alarm burst
        self.alarmburst = AlarmBurst(nodes=self.fixture.nodes, burst_id="111", burst_rate=10, duration=600, severity=2,
                                     text="acceptance text")

    def tearDown(self):
        func_test_utils.tear_down(self)

    @setup_verify(available_nodes=1)
    @func_dec("Alarm Burst", "No exceptions on successfully starting a burst")
    def test_010_start_alarm_burst_raises_no_error_when_successfully_starting_the_burst(self):
        self.alarmburst.start()

    @setup_verify(available_nodes=1)
    @func_dec("Alarm Burst", "Exception raised on failing to start a burst")
    def test_020_start_alarm_burst_raises_FailedNetsimOperation_error_exception(self):
        try:
            self.alarmburst.start()
        except FailedNetsimOperation:
            pass
        else:
            self.fail("Failed to raise FailedNetsimOperation exception")

    @setup_verify(available_nodes=1)
    @func_dec("Alarm Burst", "No exceptions on successfully stopping a burst")
    def test_030_stop_alarm_burst_raises_no_error_when_burst_is_running(self):
        self.alarmburst.stop()

if __name__ == "__main__":
    unittest2.main(verbosity=2)
