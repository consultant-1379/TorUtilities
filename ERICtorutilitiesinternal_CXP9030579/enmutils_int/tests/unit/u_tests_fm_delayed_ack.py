#!/usr/bin/env python
import unittest2
from mock import patch, Mock

from enmutils_int.lib.fm_delayed_ack import FmDelayedAck
from testslib import unit_test_utils


class FmNbiUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.fm_delayed_ack.update_pib_parameter_on_enm")
    def test_enable_delayed_acknowledgement_on_enm__is_successful(self, *_):
        FmDelayedAck().enable_delayed_acknowledgement_on_enm()

    @patch("enmutils_int.lib.fm_delayed_ack.update_pib_parameter_on_enm")
    def test_disable_delayed_acknowledgement_on_enm__is_successful(self, *_):
        FmDelayedAck().disable_delayed_acknowledgement_on_enm()

    @patch("enmutils_int.lib.fm_delayed_ack.update_pib_parameter_on_enm")
    def test_update_check_interval_for_delayed_acknowledge_on_enm__is_successful(self, *_):
        FmDelayedAck().update_check_interval_for_delayed_acknowledge_on_enm()

    @patch("enmutils_int.lib.fm_delayed_ack.update_pib_parameter_on_enm")
    def test_update_the_delay_in_hours_on_enm__is_successful(self, *_):
        FmDelayedAck().update_the_delay_in_hours_on_enm()

    @patch("enmutils_int.lib.fm_delayed_ack.FmDelayedAck.update_the_delay_in_hours_on_enm")
    def test_reset_delay_to_default_value_on_enm__is_successful(self, *_):
        FmDelayedAck().reset_delay_to_default_value_on_enm()

    @patch("enmutils_int.lib.fm_delayed_ack.FmDelayedAck.update_check_interval_for_delayed_acknowledge_on_enm")
    def test_reset_delayed_ack_check_interval_to_default_value_on_enm(self, *_):
        FmDelayedAck().reset_delayed_ack_check_interval_to_default_value_on_enm()

    @patch("enmutils_int.lib.fm_delayed_ack.FmDelayedAck.disable_delayed_acknowledgement_on_enm")
    def test__teardown__is_successful(self, *_):
        FmDelayedAck()._teardown()

    @patch("enmutils_int.lib.fm_delayed_ack.FmDelayedAck.disable_delayed_acknowledgement_on_enm", side_effect=Exception)
    @patch("enmutils_int.lib.fm_delayed_ack.log.logger.debug")
    def test__teardown__logs_error_if_exception_encountered_disabling_ack_on_enm(self, mock_debug, *_):
        FmDelayedAck()._teardown()
        self.assertTrue(mock_debug.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
