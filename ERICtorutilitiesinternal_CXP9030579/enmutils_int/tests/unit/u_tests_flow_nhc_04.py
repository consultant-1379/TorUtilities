#!/usr/bin/env python
import unittest2
from requests.exceptions import HTTPError
from enmutils.lib.exceptions import EnmApplicationError
from enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow import Nhc04
from mock import Mock, patch, PropertyMock
from testslib import unit_test_utils

radio_node_package = {u'productRelease': None, u'packageName': u'CXP9024418_6_R2CXS2', u'productRevision': u'R2CXS2',
                      u'productData': u'CXP9024418/6_R2CXS2', u'productNumber': u'CXP9024418/6'}


class NHC04FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock(username='NHC_04')
        self.nodes = [Mock(), Mock()]
        self.nhc_04 = Nhc04()
        self.nhc_04.NUM_USERS = 1
        self.nhc_04.USER_ROLES = ["Nhc_Administrator", "Shm_Administrator"]
        self.nhc_04.SCHEDULED_DAYS = "THURSDAY"
        self.nhc_04.SCHEDULED_TIMES_STRINGS = ["04:30:00"]
        self.nhc_04.NHC_JOB_TIME = "05:00:00"

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.get_time_from_enm_return_string_with_gtm_offset')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.state', new_callable=PropertyMock())
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.create_users', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.get_existing_health_check_profiles')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.create_new_health_check_profile')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.create_nhc_job')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.keep_running')
    def test_execute_nhc_04_flow__success_if_exists(self, mock_keep_running, mock_create_nhc_job, mock_create_profile,
                                                    mock_existing, *_):
        mock_keep_running.side_effect = [True, False]
        mock_create_profile.return_value = "HealthCheckProfile_administrator_03082020133401"
        mock_existing.return_value = ["HealthCheckProfile_administrator_03082020133401"]
        self.nhc_04.execute_nhc_04_flow()
        self.assertEqual(mock_create_profile.call_count, 1)
        self.assertTrue(mock_create_nhc_job.called)

    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.get_time_from_enm_return_string_with_gtm_offset')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.state', new_callable=PropertyMock())
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.create_users', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.get_existing_health_check_profiles')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.create_new_health_check_profile')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.create_nhc_job')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.keep_running')
    def test_execute_nhc_04_flow__success_if_not_exists(self, mock_keep_running, mock_create_nhc_job,
                                                        mock_create_profile, mock_existing, *_):
        mock_keep_running.side_effect = [True, False]
        mock_create_profile.return_value = "HealthCheckProfile_administrator_03082020133401"
        mock_existing.return_value = []
        self.nhc_04.execute_nhc_04_flow()
        self.assertEqual(mock_create_profile.call_count, 2)
        self.assertTrue(mock_create_nhc_job.called)

    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.time.sleep')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.load_mgr.wait_for_setup_profile')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.state', new_callable=PropertyMock())
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.create_users', return_value=[Mock()])
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.get_time_from_enm_return_string_with_gtm_offset')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.get_existing_health_check_profiles')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.create_new_health_check_profile')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.create_nhc_job')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.keep_running')
    def test_execute_nhc_04_flow__exception(self, mock_keep_running, mock_create_nhc_job, mock_create_profile,
                                            mock_existing, mock_add_error, *_):
        mock_keep_running.side_effect = [True, True, False]
        mock_create_profile.return_value = "HealthCheckProfile_administrator_03082020133401"
        mock_existing.return_value = ["HealthCheckProfile_administrator_03082020133401"]
        mock_create_nhc_job.side_effect = Exception
        self.nhc_04.execute_nhc_04_flow()
        self.assertEqual(mock_create_profile.call_count, 1)
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.get_nodes_list_by_attribute')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.sleep_until_day')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.state', new_callable=PropertyMock())
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.get_time_from_enm_return_string_with_gtm_offset')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.create_new_health_check_profile')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.create_users')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.keep_running')
    def test_execute_nhc_04_flow__exception_while_getting_time(self, mock_keep_running, mock_create_users,
                                                               mock_create_profile, mock_get_time, mock_add_error, *_):
        mock_keep_running.side_effect = [True, False]
        mock_user = Mock()
        mock_create_users.return_value = [mock_user]
        mock_create_profile.return_value = "HealthCheckProfile_administrator_03082020133401"
        mock_get_time.side_effect = EnvironmentError
        self.nhc_04.execute_nhc_04_flow()
        self.assertTrue(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.create_nhc_profile')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.get_radio_node_package')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.SoftwareOperations')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.SoftwarePackage')
    def test_create_new_health_check_profile__success(self, mock_software_package, mock_software_operations,
                                                      mock_get_radio_package, mock_create_nhc_profile):
        package = Mock()
        package.name = "CXP"
        mock_software_package.return_value = package
        mock_get_radio_package.return_value = radio_node_package
        mock_create_nhc_profile.return_value = 'NHC_04_'
        self.nhc_04.create_new_health_check_profile(self.user, self.nodes)
        mock_software_package.assert_called_with(self.nodes, self.user, use_default=True, profile_name=self.nhc_04.NAME)
        mock_software_operations.assert_called_with(user=self.user, package=package, ptype=self.nodes[0].primary_type)
        mock_create_nhc_profile.assert_called_with(self.user, self.nodes[0].primary_type, radio_node_package,
                                                   self.nhc_04.NAME)

    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.add_error_as_exception')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.create_nhc_profile')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.get_radio_node_package')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.SoftwareOperations')
    @patch('enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.SoftwarePackage')
    def test_create_new_health_check_profile__raises_exception(self, mock_software_package, mock_software_operations,
                                                               mock_get_radio_package, mock_create_nhc_profile, mock_add_error):
        package = Mock()
        package.name = "CXP"
        mock_software_package.return_value = package
        mock_get_radio_package.side_effect = EnmApplicationError
        self.nhc_04.create_new_health_check_profile(self.user, self.nodes)
        mock_software_package.assert_called_with(self.nodes, self.user, use_default=True, profile_name=self.nhc_04.NAME)
        mock_software_operations.assert_called_with(user=self.user, package=package, ptype=self.nodes[0].primary_type)
        self.assertEqual(mock_add_error.call_count, 1)
        self.assertEqual(mock_create_nhc_profile.call_count, 0)

    def test_get_existing_health_check_profiles__success(self):
        self.user.post.return_value.json.return_value = {u'profileList': [{u'status': u'', u'name': u'NHC_04_HealthCheckProfile'}]}
        expected_output = ['NHC_04_HealthCheckProfile']
        self.assertEqual(expected_output, self.nhc_04.get_existing_health_check_profiles(self.user))

    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.add_error_as_exception")
    def test_get_existing_health_check_profiles__http_error(self, mock_add_error_as_exception):
        self.user.post.side_effect = HTTPError
        self.nhc_04.get_existing_health_check_profiles(self.user)
        self.assertTrue(mock_add_error_as_exception.called)

    @patch("enmutils_int.lib.profile_flows.nhc_flows.nhc_04_flow.Nhc04.add_error_as_exception")
    def test_get_existing_health_check_profiles__exception(self, mock_add_error_as_exception):
        self.user.post.side_effect = Exception
        self.nhc_04.get_existing_health_check_profiles(self.user)
        self.assertTrue(mock_add_error_as_exception.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
