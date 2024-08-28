#!/usr/bin/env python
import unittest2
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils_int.lib.profile_flows.pm_flows.pm57profile import (chunks, retrieve_ulsa_files, get_files_summary_list,
                                                                 get_spectrum_data, Pm57Profile)
from enmutils_int.lib.workload.pm_57 import PM_57
from mock import patch, Mock, PropertyMock
from testslib import unit_test_utils


class Pm57ProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()

        self.user = Mock(username="TestUser")
        self.profile = Pm57Profile()
        self.profile.USER_ROLES = ['ULSA_Operator']
        self.profile.NUM_USERS = 10
        self.profile.MAX_NUMBER_OF_FILES_TO_BE_FETCHED = 40
        self.profile.SAMPLING_PERIODS = 4
        self.profile.TIME_BETWEEN_SAMPLING_PERIODS_MINS = 15

    def tearDown(self):
        unit_test_utils.tear_down()

    # chunks tests

    def test_good_chunks_generator(self):
        n_users = 4
        elements = [i for i in xrange(40)]

        first = list(chunks(elements, n_users))
        self.assertEqual(len(first), 10)
        self.assertEqual(len(first[0]), 4)
        self.assertEqual(len(first[9]), 4)

        n_users = 5
        second = list(chunks(elements, n_users))
        self.assertEqual(len(second), 8)
        self.assertEqual(len(second[0]), 5)
        self.assertEqual(len(second[7]), 5)

    def test_chunks_generator_limits(self):
        n_users = 3
        elements = [i for i in xrange(40)]

        first = list(chunks([], n_users))
        self.assertEqual(len(first), 0)

        n_users = 10
        second = list(chunks(elements, n_users))
        self.assertEqual(len(second), 4)
        self.assertEqual(len(second[0]), 10)
        self.assertEqual(len(second[3]), 10)

        n_users = 1
        third = list(chunks(elements, n_users))
        self.assertEqual(len(third), 40)
        self.assertEqual(len(third[0]), 1)
        self.assertEqual(len(third[39]), 1)

    # get_files_summary_list tests

    def test_good_get_files_summary_list(self):
        ulsa_response = Mock()
        ulsa_response.ok = True
        json_data = [{'networkelement': 'NE'}]
        ulsa_response.json.return_value = json_data

        self.user.get.return_value = ulsa_response
        summary = get_files_summary_list(self.user)
        self.assertEqual(summary, json_data)

    def test_bad_response_get_files_summary_list(self):
        ulsa_response = Mock()
        ulsa_response.ok = False
        json_data = [{'networkelement': 'NE'}]
        ulsa_response.json.return_value = json_data

        self.user.get.return_value = ulsa_response
        with self.assertRaises(EnmApplicationError) as application_error:
            get_files_summary_list(self.user)
        self.assertEqual('Error retrieving the files summary.', application_error.exception.message)

    def test_empty_response_get_files_summary_list(self):
        ulsa_response = Mock()
        ulsa_response.ok = False
        json_data = []
        ulsa_response.json.return_value = json_data

        self.user.get.return_value = ulsa_response
        with self.assertRaises(EnmApplicationError) as application_error:
            get_files_summary_list(self.user)
        self.assertEqual('Error retrieving the files summary.', application_error.exception.message)

    # retrieve_ulsa_files tests

    def test_retrieve_ulsa_files_is_successful_using_one_ne(self):
        ulsa_response = Mock()
        ulsa_response.ok = True
        json_data = [{'filepath': '/path{}'.format(i)} for i in xrange(50)]
        ulsa_response.json.return_value = json_data

        self.user.get.return_value = ulsa_response
        summary = [{'networkelement': 'NE1', 'radiounit': '1', 'port': '1'},
                   {'networkelement': 'NE2', 'radiounit': '1', 'port': '1'}]
        files = retrieve_ulsa_files(self.user, summary, 40)
        self.assertEqual(len(files), 40)

    def test_retrieve_ulsa_files__is_successful_using_more_than_one_ne(self):
        ulsa_response = Mock()
        ulsa_response.ok = True
        json_data = [{'filepath': '/path{}'.format(i)} for i in xrange(25)]
        ulsa_response.json.return_value = json_data

        self.user.get.return_value = ulsa_response
        summary = [{'networkelement': 'NE1', 'radiounit': '1', 'port': '1'},
                   {'networkelement': 'NE2', 'radiounit': '1', 'port': '1'}]
        files = retrieve_ulsa_files(self.user, summary, 40)
        self.assertEqual(len(files), 40)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm57profile.time.sleep")
    def test_retrieve_ulsa_files__is_unsuccessful_for_first_ne(self, *_):
        self.user.get.return_value.ok = False
        self.user.get.side_effect = Exception("Cannot retrieve UlSA files for first NE")
        summary = [{'networkelement': 'NE1', 'radiounit': '1', 'port': '1'},
                   {'networkelement': 'NE2', 'radiounit': '1', 'port': '1'}]
        response = retrieve_ulsa_files(self.user, summary, 40)
        self.assertFalse(response)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm57profile.time.sleep")
    def test_retrieve_ulsa_files__is_unsuccessful_for_second_ne(self, *_):
        ulsa_response = Mock()
        ulsa_response.ok = True
        json_data = [{'filepath': '/path{}'.format(i)} for i in xrange(25)]
        ulsa_response.json.return_value = json_data

        self.user.get.side_effect = [ulsa_response, Exception("Cannot retrieve UlSA files for second NE")]
        summary = [{'networkelement': 'NE1', 'radiounit': '1', 'port': '1'},
                   {'networkelement': 'NE2', 'radiounit': '1', 'port': '1'}]
        response = retrieve_ulsa_files(self.user, summary, 40)
        self.assertEqual(len(response), 25)

    # get_spectrum_data tests

    def test_good_get_spectrum_data(self):
        user_files = (self.user, 'filename1')
        self.user.get.return_value.ok = True
        self.user.get.json.return_value = {'filepath1': 'path1'}
        get_spectrum_data(user_files)

    def test_error_get_spectrum_data(self):
        user_files = (self.user, 'filename1')
        self.user.get.side_effect = Exception("UlSA Samples not retrieved")
        with self.assertRaises(EnvironError) as environ_error:
            get_spectrum_data(user_files)
        self.assertEqual("USER TestUser: Error retrieving Spectrum sample data for file: 'filename1' "
                         "- UlSA Samples not retrieved",
                         environ_error.exception.message)

    def test_bad_state_get_spectrum_data(self):
        user_files = (self.user, 'filename1')
        self.user.get.return_value.ok = False
        with self.assertRaises(EnmApplicationError) as application_error:
            get_spectrum_data(user_files)
        self.assertEqual("USER TestUser: Response NOK retrieving Spectrum sample data for file: 'filename1'",
                         application_error.exception.message)

    def test_empty_response_get_spectrum_data(self):
        user_files = (self.user, 'filename1')
        self.user.get.return_value.ok = True
        self.user.get.return_value.json.return_value = {}
        with self.assertRaises(EnvironError) as environ_error:
            get_spectrum_data(user_files)
        self.assertEqual("USER TestUser: Empty output retrieving Spectrum sample data for file: 'filename1'",
                         environ_error.exception.message)

    # get_users_filename_lists tests

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.get_files_summary_list')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.retrieve_ulsa_files')
    def test_get_users_filename_lists__is_successful_if_less_than_max_files_found(
            self, mock_retrieve_ulsa_files, mock_get_files_summary_list, mock_add_exception):
        mock_retrieve_ulsa_files.return_value = ['/path{}'.format(i) for i in xrange(25)]
        users = [self.user for _ in xrange(10)]
        filename_lists = self.profile.get_users_filename_lists(users, 4)
        self.assertTrue(mock_get_files_summary_list.called)
        self.assertFalse(mock_add_exception.called)
        self.assertEqual(len(filename_lists), 4)
        for filenames in filename_lists:
            self.assertEqual(len(filenames), 10)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.get_files_summary_list')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.retrieve_ulsa_files')
    def test_get_users_filename_lists__is_successful_if_more_than_max_files_found(
            self, mock_retrieve_ulsa_files, mock_get_files_summary_list, mock_add_exception):
        mock_retrieve_ulsa_files.return_value = ['/path{}'.format(i) for i in xrange(50)]
        users = [self.user for _ in xrange(10)]
        filename_lists = self.profile.get_users_filename_lists(users, 4)
        self.assertTrue(mock_get_files_summary_list.called)
        self.assertFalse(mock_add_exception.called)
        self.assertEqual(len(filename_lists), 4)
        for filenames in filename_lists:
            self.assertEqual(len(filenames), 10)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.retrieve_ulsa_files')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.get_files_summary_list')
    def test_get_users_filename_lists__adds_error_if_enm_returns_empty_list(
            self, mock_get_summary, mock_add_exception, mock_retrieve_ulsa_files):
        mock_retrieve_ulsa_files.return_value = []
        users = [self.user for _ in xrange(10)]
        mock_get_summary.return_value = [Mock, Mock]
        filename_lists = self.profile.get_users_filename_lists(users, 4)
        self.assertTrue(mock_add_exception.called)
        self.assertFalse(filename_lists)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.retrieve_ulsa_files')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.get_files_summary_list')
    def test_get_users_filename_lists__adds_exception_if_enm_throws_errors(
            self, mock_get_summary, mock_add_exception, *_):
        mock_get_summary.side_effect = EnmApplicationError("Error retrieving the files summary.")
        users = [self.user for _ in xrange(10)]
        filename_lists = self.profile.get_users_filename_lists(users, 4)
        self.assertTrue(mock_add_exception.called)
        self.assertFalse(filename_lists)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.get_files_summary_list')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.retrieve_ulsa_files')
    def test_get_users_filename_lists__adds_exception_when_no_files_retrieved_from_enm(
            self, mock_retrieve_ulsa_files, mock_add_exception, *_):
        users = [self.user for _ in xrange(10)]
        mock_retrieve_ulsa_files.return_value = []
        filename_lists = self.profile.get_users_filename_lists(users, 4)
        self.assertTrue(mock_add_exception.called)
        self.assertFalse(filename_lists)

    # process_ulsa_files tests

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm57profile.time.sleep")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.create_and_execute_threads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.get_users_filename_lists")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm57profile.get_spectrum_data")
    def test_process_ulsa_files__is_successful(
            self, mock_get_spectrum_data, mock_get_users_filename_lists, mock_create_and_execute_threads,
            mock_add_error_as_exception, *_):
        mock_get_users_filename_lists.return_value = [['filename_A{}'.format(i), 'filename_B{}'.format(i)]
                                                      for i in xrange(4)]
        self.profile.process_ulsa_files([self.user] * 2, 4, 15)
        self.assertEqual(4, mock_get_users_filename_lists.call_count)
        self.assertEqual(4, mock_create_and_execute_threads.call_count)
        mock_get_users_filename_lists.assert_called_with([self.user] * 2, 4)
        mock_create_and_execute_threads.assert_called_with([(self.user, "filename_A3"), (self.user, "filename_B3")],
                                                           2, func_ref=mock_get_spectrum_data)
        self.assertFalse(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.time.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.create_and_execute_threads')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.get_users_filename_lists')
    def test_process_ulsa_files__is_successful_when_enm_returns_empty_list(
            self, mock_get_users_filename_lists, mock_create_and_execute_threads, *_):

        mock_get_users_filename_lists.return_value = []

        self.profile.process_ulsa_files([self.user] * 2, 4, 15)
        self.assertEqual(4, mock_get_users_filename_lists.call_count)
        self.assertFalse(mock_create_and_execute_threads.called)

    # execute_flow tests

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.time.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.sleep_until_time')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.create_profile_users")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.keep_running")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.process_ulsa_files")
    def test_execute_flow__is_successful(
            self, mock_process_ulsa_files, mock_keep_running, mock_create_profile_users, *_):
        mock_keep_running.side_effect = [True, False]
        users = [Mock, Mock]
        mock_create_profile_users.return_value = users
        self.profile.execute_flow()
        mock_process_ulsa_files.assert_called_with(users, 4, 15)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.time.sleep')
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.sleep_until_time')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.create_profile_users")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.add_error_as_exception')
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.keep_running")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.process_ulsa_files")
    def test_execute_flow__adds_error_is_processing_is_unsuccessful(
            self, mock_process_ulsa_files, mock_keep_running, mock_add_error_as_exception, *_):
        mock_keep_running.side_effect = [True, False]
        mock_process_ulsa_files.side_effect = Exception
        self.profile.execute_flow()
        self.assertTrue(mock_process_ulsa_files.called)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm57profile.Pm57Profile.execute_flow')
    def test_run__doesnt_raise_exception_in_pm57(self, _):
        pm57 = PM_57()
        pm57.run()


if __name__ == "__main__":
    unittest2.main(verbosity=2)
