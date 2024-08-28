#!/usr/bin/env python
import unittest2

from mock import patch, Mock, PropertyMock
from testslib import unit_test_utils

from enmutils_int.lib.profile_flows.pm_flows.pm15profile import Pm15Profile
from enmutils_int.lib.workload import pm_15
from enmutils.lib.exceptions import EnvironError


class Pm15ProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.user = Mock()
        self.pm_15 = pm_15.PM_15()
        self.profile = Pm15Profile()
        self.profile.POLLING_AND_MASTER_RETENTION = ('param', 666)
        self.profile.SCHEDULE_SLEEP = 1

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm15profile.Pm15Profile.execute_flow')
    def test_run__in_pm_15_is_successful(self, mock_execute_flow):
        self.pm_15.run()
        self.assertTrue(mock_execute_flow.called)

    # execute_flow tests

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm15profile.Pm15Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm15profile.Pm15Profile.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm15profile.log.logger.debug')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm15profile.get_pib_value_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm15profile.Pm15Profile.keep_running')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm15profile.Pm15Profile.add_error_as_exception')
    def test_execute_flow__is_successful(self, mock_add_exception, mock_keep_running, mock_get_pib_value_on_enm,
                                         mock_log_debug, *_):
        mock_keep_running.side_effect = [True, False]
        mock_get_pib_value_on_enm.return_value = '666'
        self.profile.execute_flow()
        self.assertTrue(mock_get_pib_value_on_enm.called)
        self.assertFalse(mock_add_exception.called)
        self.assertTrue(mock_keep_running.called)
        self.assertTrue(mock_log_debug.call_count, 8)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm15profile.Pm15Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm15profile.Pm15Profile.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm15profile.get_pib_value_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm15profile.Pm15Profile.keep_running')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm15profile.Pm15Profile.add_error_as_exception')
    def test_execute_flow__if_setting_value_is_incorrect(self, mock_add_exception, mock_keep_running,
                                                         mock_get_pib_value_on_enm, *_):
        mock_get_pib_value_on_enm.return_value = '123'
        mock_keep_running.side_effect = [True, False]
        self.profile.execute_flow()
        self.assertTrue(mock_add_exception.called)
        self.assertTrue(mock_get_pib_value_on_enm.called)
        self.assertTrue(mock_keep_running.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm15profile.Pm15Profile.state', new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm15profile.Pm15Profile.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm15profile.get_pib_value_on_enm')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm15profile.Pm15Profile.keep_running')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm15profile.Pm15Profile.add_error_as_exception')
    def test_execute_flow__raises_EnvironError_when_calling_fetch_pib_parameter_value(self, mock_add_exception,
                                                                                      mock_keep_running,
                                                                                      mock_get_pib_value_on_enm,
                                                                                      *_):
        mock_get_pib_value_on_enm.side_effect = Exception(EnvironError("Unable to determine IP of "
                                                                       "application service from global "
                                                                       "properties file on ENM: pmserv"))
        mock_keep_running.side_effect = [True, False]
        self.profile.execute_flow()
        self.assertTrue(mock_add_exception.called)
        self.assertTrue(mock_keep_running.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
