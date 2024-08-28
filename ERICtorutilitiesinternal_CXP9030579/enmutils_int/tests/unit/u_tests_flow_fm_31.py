#!/usr/bin/env python

import unittest2
from testslib import unit_test_utils
from mock import patch, PropertyMock
from enmutils_int.lib.profile_flows.fm_flows.fm_31_flow import Fm31


class Fm31UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.flow = Fm31()
        self.flow.SERVICE = 'fmalarmprocessing'
        self.flow.PARAMETERS = [('alarmOverloadProtectionOn', 'true'), ('alarmOverloadProtectionThreshold', '55200'),
                                ('alarmOverloadProtectionLowerThreshold', '70')]
        self.service_locations = ['svc-3-fmalarmprocessing', 'svc-5-fmalarmprocessing']

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_31_flow.Fm31.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_31_flow.log")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_31_flow.get_pib_value_on_enm")
    def test_execute_flow__does_not_modify_parameter_values_if_they_are_correct(
            self, mock_get_pib_value_on_enm, mock_log, *_):
        mock_get_pib_value_on_enm.side_effect = ['true', '55200', '70']
        self.flow.execute_flow()
        self.assertEqual(mock_get_pib_value_on_enm.call_count, 3)
        self.assertEqual(mock_log.logger.info.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_31_flow.Fm31.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_31_flow.log")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_31_flow.get_pib_value_on_enm")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_31_flow.update_pib_parameter_on_enm")
    def test_execute_flow__modifies_parameter_values_if_they_are_not_correct(
            self, mock_update_pib_parameter_on_enm, mock_get_pib_value_on_enm, mock_log, *_):
        mock_get_pib_value_on_enm.side_effect = ['true', '48000', '50']
        self.flow.execute_flow()
        self.assertEqual(mock_get_pib_value_on_enm.call_count, 3)
        self.assertEqual(mock_update_pib_parameter_on_enm.call_count, 2)
        self.assertEqual(mock_log.logger.info.call_count, 5)

    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_31_flow.Fm31.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_31_flow.Fm31.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_31_flow.log")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_31_flow.get_pib_value_on_enm")
    @patch("enmutils_int.lib.profile_flows.fm_flows.fm_31_flow.update_pib_parameter_on_enm")
    def test_execute_flow__adds_exception_if_parameter_modification_fails(
            self, mock_update_pib_parameter_on_enm, mock_get_pib_value_on_enm, mock_log, mock_add_error, *_):
        mock_get_pib_value_on_enm.side_effect = ['true', '48000', '50']
        mock_update_pib_parameter_on_enm.side_effect = Exception
        self.flow.execute_flow()
        self.assertEqual(mock_get_pib_value_on_enm.call_count, 3)
        self.assertEqual(mock_update_pib_parameter_on_enm.call_count, 2)
        self.assertEqual(mock_add_error.call_count, 2)
        self.assertEqual(mock_log.logger.info.call_count, 5)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
