#!/usr/bin/env python
import unittest2
from mock import Mock, patch, PropertyMock

from enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow import CmExport16, HTTPError
from testslib import unit_test_utils


class CmExport16UnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock()
        self.flow = CmExport16()
        self.flow.NAME = "CMEXPORT_16"
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ['Cmedit_Operator', 'Shm_Administrator']

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.CmExport16.create_save_search',
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.CmExport16.identifier',
           new_callable=PropertyMock, return_value='CMEXPORT_16_0723-15281002')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.CmExport16.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.CmExport16.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.ShmExport')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.CmExport16.create_profile_users')
    def test_execute_flow__is_successful(self, mock_user, mock_shm_export, *_):
        mock_user.return_value = [self.user]
        self.flow.execute_flow()
        mock_shm_export.assert_called_with(user=self.user, export_type='lic', name='CMEXPORT_16_0723-15281002',
                                           saved_search_name='cmexport_16_saved_search')
        self.assertEqual(mock_shm_export.return_value.validate.call_count, 3)
        self.assertEqual(mock_shm_export.return_value.create.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.CmExport16.create_save_search',
           return_value=True)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.CmExport16.identifier',
           new_callable=PropertyMock, return_value='CMEXPORT_16_0723-15281002')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.CmExport16.sleep_until_time')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.CmExport16.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.ShmExport')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.CmExport16.create_profile_users')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.GenericFlow.add_error_as_exception')
    def test_execute_flow__create_adds_error_as_exception(self, mock_add_error, mock_user, mock_shm_export, *_):
        mock_user.return_value = [self.user]
        mock_shm_export.return_value.create.side_effect = Exception
        self.flow.execute_flow()
        self.assertEqual(mock_add_error.call_count, 3)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.CmExport16.create_save_search',
           side_effect=[HTTPError("Error"), True])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.CmExport16.identifier',
           new_callable=PropertyMock, return_value='CMEXPORT_16_0723-15281002')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.CmExport16.keep_running',
           side_effect=[True, False])
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.CmExport16.sleep_until_time')
    @patch('time.sleep', return_value=0)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.ShmExport')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.CmExport16.create_profile_users')
    def test_execute_flow__sleeps_if_saved_search_failure(self, mock_user, mock_shm_export, mock_sleep, *_):
        mock_user.return_value = [self.user]
        self.flow.execute_flow()
        mock_shm_export.assert_called_with(user=self.user, export_type='lic', name='CMEXPORT_16_0723-15281002',
                                           saved_search_name='cmexport_16_saved_search')
        self.assertEqual(mock_shm_export.return_value.validate.call_count, 3)
        self.assertEqual(mock_shm_export.return_value.create.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.Search.exists', return_value=True,
           new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.Search.delete')
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.Search.save')
    def test_create_save_search__success(self, *_):
        self.assertTrue(self.flow.create_save_search(Mock()))

    @patch('time.sleep', return_value=lambda _: None)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.Search.exists',
           side_effect=[True, False], new_callable=PropertyMock)
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.Search.delete',
           side_effect=HTTPError("Error"))
    @patch('enmutils_int.lib.profile_flows.cmexport_flows.cmexport_16_flow.Search.save',
           side_effect=[HTTPError("Error"), None])
    def test_create_save_search__retries_on_http_error(self, *_):
        self.assertTrue(self.flow.create_save_search(Mock()))


if __name__ == "__main__":
    unittest2.main(verbosity=2)
