#!/usr/bin/env python
import unittest2

from enmutils_int.lib.fm_delayed_ack import FmDelayedAck
from testslib import func_test_utils, test_fixture
from testslib.func_test_utils import func_dec


class FmDelayedAckTests(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.fixture = test_fixture.AcceptanceTestFixture(cls)

    @classmethod
    def tearDownClass(cls):
        func_test_utils.module_tear_down(cls)

    def setUp(self):
        func_test_utils.setup(self)
        self.delayed_ack = FmDelayedAck()
        self.delayed_ack_two = FmDelayedAck(vm_addresses=['not_a_valid_ip_address'])

    def tearDown(self):
        func_test_utils.tear_down(self)

    @func_dec("Fm_Delayed_Ack", "Enable delayed ack")
    def test_01_fm_delayed_ack_enable(self):
        self.delayed_ack.enable_delayed_acknowledgement_on_enm()

    @func_dec("Fm_Delayed_Ack", "Disable delayed ack")
    def test_03_test_delayed_ack_disable(self):
        self.delayed_ack.disable_delayed_acknowledgement_on_enm()

    @func_dec("Fm_Delayed_Ack", "Update check interval")
    def test_05_test_update_check_interval_for_delayed_acknowledge(self):
        self.delayed_ack.update_check_interval_for_delayed_acknowledge_on_enm()

    @func_dec("Fm_Delayed_Ack", "Update delay in hours")
    def test_07_test_update_delay_in_hours(self):
        self.delayed_ack.update_the_delay_in_hours_on_enm()

    @func_dec("Fm_Delayed_Ack", "Reset interval")
    def test_09_test_reset_interval_to_default_on_enm(self):
        self.delayed_ack.reset_delayed_ack_check_interval_to_default_value_on_enm()

    @func_dec("Fm_Delayed_Ack", "Reset delay")
    def test_10_test_reset_delay_to_default_value_on_enm(self):
        self.delayed_ack.reset_delay_to_default_value_on_enm()

    @func_dec("Fm_Delayed_Ack", "Teardown delayed ack")
    def test_11_test_teardown(self):
        self.delayed_ack._teardown()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
