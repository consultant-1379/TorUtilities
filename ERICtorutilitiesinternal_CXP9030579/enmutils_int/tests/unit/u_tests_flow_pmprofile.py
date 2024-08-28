#!/usr/bin/env python
import unittest2
from enmutils_int.lib.profile_flows.pm_flows import pmprofile
from mock import patch, Mock
from testslib import unit_test_utils


class PmProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.profile = pmprofile.PmProfile()
        self.CMD = ("{sudo}/ericsson/pib-scripts/etc/config.py read --app_server_address={app_address}:8080 "
                    "--name={parameter}")

    def tearDown(self):
        unit_test_utils.tear_down()

    # show_errored_threads TESTS ######################################################################################

    @patch("enmutils_int.lib.profile.Profile.add_error_as_exception")
    def test_process_thread_no_errors(self, mock_add_exception):
        n_threads = 10
        thread_result = Mock()
        thread_result.work_entries = [Mock(exception_raised=False) for _ in xrange(n_threads)]
        self.profile.show_errored_threads(thread_result, n_threads, Exception)
        self.assertFalse(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmprofile.PmProfile.add_error_as_exception")
    def test_process_thread_with_errors(self, mock_add_exception):
        n_threads = 10
        thread_result = Mock()
        thread_result.work_entries = [Mock(exception_raised=False) for _ in xrange(9)] + [Mock(exception_raised=True)]
        self.profile.show_errored_threads(thread_result, n_threads, Exception)
        self.assertTrue(mock_add_exception.called)

    # check_pmic_retention_period TESTS ################################################################################

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmprofile.get_pib_value_on_enm", return_value="4320")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmprofile.PmProfile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmprofile.log.logger.debug")
    def test_check_pmic_retention_periods__successfully_retrieves_the_correct_value(
            self, mock_logger_debug, mock_add_error_as_exception, *_):
        self.profile.check_pmic_retention_period(("pmicCelltraceFileRetentionPeriodInMinutes", 4320))
        mock_logger_debug.assert_called_with("The Retention period for 'pmicCelltraceFileRetentionPeriodInMinutes' of "
                                             "'4320' was correct.")
        self.assertFalse(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmprofile.get_pib_value_on_enm", return_value="1440")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmprofile.EnvironError")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmprofile.PmProfile.add_error_as_exception")
    def test_check_pmic_retention_periods__adds_an_error_as_an_exception_if_pib_value_set_to_non_default_value(
            self, mock_add_error_as_exception, mock_environerror, *_):
        self.profile.check_pmic_retention_period(("pmicCelltraceFileRetentionPeriodInMinutes", 4320))
        mock_environerror.assert_called_with(
            "The 'pmicCelltraceFileRetentionPeriodInMinutes' retention period of: '1440' minutes does not "
            "match the expected default of: '4320' minutes.")
        self.assertEqual(mock_add_error_as_exception.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pmprofile.get_pib_value_on_enm", return_value="")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmprofile.EnmApplicationError")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pmprofile.PmProfile.add_error_as_exception")
    def test_check_pmic_retention_periods__adds_an_error_as_an_exception_if_pib_not_set(
            self, mock_add_error_as_exception, mock_enmapplicationerror, *_):
        self.profile.check_pmic_retention_period(("pmicCelltraceFileRetentionPeriodInMinutes", 4320))
        mock_enmapplicationerror.assert_called_with("Could not get the value of the "
                                                    "'pmicCelltraceFileRetentionPeriodInMinutes'.")
        self.assertEqual(mock_add_error_as_exception.call_count, 1)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
