#!/usr/bin/env python
import unittest2

from mock import patch, Mock, PropertyMock, call
from testslib import unit_test_utils

from enmutils.lib.exceptions import EnvironError, EnmApplicationError
from enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow import Ftpes01Flow


class Ftpes01FlowUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        unit_test_utils.setup()
        self.flow = Ftpes01Flow()
        self.flow.MAX_POLL = 4
        oss_prefix = "SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement="
        self.nodes_list = [Mock(node_id='123', primary_type="RadioNode", netsim="netsim_120", profiles=['FTPES_01'],
                                oss_prefix="{0}123".format(oss_prefix)),
                           Mock(node_id="132", primary_type="RadioNode", netsim="netsim_120", profiles=['FTPES_01'],
                                oss_prefix="{0}132".format(oss_prefix)),
                           Mock(node_id="456", primary_type="RadioNode", netsim="netsim_210", profiles=['FTPES_01'],
                                oss_prefix="{0}456".format(oss_prefix)),
                           Mock(node_id="987", primary_type="RadioNode", netsim="netsim_210", profiles=['FTPES_01'],
                                oss_prefix="{0}987".format(oss_prefix))]
        self.netsims_with_nodes = {"netsim_120": self.nodes_list[:2], "netsim_210": self.nodes_list[2:4]}
        self.flow.NUM_USERS = 1
        self.flow.USER_ROLES = ['ADMINISTRATOR']
        self.flow.NUM_NODES_PER_BATCH = 2
        self.flow.NETWORK_PERCENT = 0.5
        self.flow.JOB_STATUS_CHECK_INTERVAL = 60
        self.flow.user = Mock()

    def tearDown(self):
        unit_test_utils.tear_down()

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.toggle_ftpes")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.ftpes_profile_prerequisites")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.create_profile_users")
    def test_execute_flow__is_successful(self, mock_create_users, mock_nodes_list, mock_netsim_nodes, mock_toggle_ftpes,
                                         mock_add_error, *_):
        mock_create_users.return_value = [self.user]
        mock_nodes_list.return_value = self.nodes_list
        mock_netsim_nodes.return_value = self.nodes_list
        self.flow.execute_flow()
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_netsim_nodes.called)
        self.assertTrue(mock_nodes_list.called)
        mock_toggle_ftpes.assert_called_with(self.nodes_list)
        self.assertFalse(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.toggle_ftpes")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.ftpes_profile_prerequisites")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.create_profile_users")
    def test_execute_flow__if_nodes_are_not_allocated_to_profile(self, mock_create_users, mock_nodes_list,
                                                                 mock_netsim_nodes, mock_toggle_ftpes, mock_add_error,
                                                                 *_):
        mock_create_users.return_value = [self.user]
        mock_nodes_list.return_value = []
        self.flow.execute_flow()
        self.assertTrue(mock_create_users.called)
        self.assertFalse(mock_netsim_nodes.called)
        self.assertTrue(mock_nodes_list.called)
        self.assertFalse(mock_toggle_ftpes.called)
        message = "Profile is not allocated to any node"
        self.assertTrue(call(EnvironError(message) in mock_add_error.mock_calls))

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.toggle_ftpes")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.ftpes_profile_prerequisites")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.create_profile_users")
    def test_execute_flow__raise_env_error_while_calling_ftpes_profile_prerequisites(self, mock_create_users,
                                                                                     mock_nodes_list, mock_netsim_nodes,
                                                                                     mock_toggle_ftpes, mock_add_error,
                                                                                     *_):
        mock_create_users.return_value = [self.user]
        mock_nodes_list.return_value = self.nodes_list
        mock_netsim_nodes.side_effect = EnvironError("Synced nodes are not available")
        self.flow.execute_flow()
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_nodes_list.called)
        self.assertTrue(mock_netsim_nodes.called)
        self.assertFalse(mock_toggle_ftpes.called)
        self.assertTrue(call(mock_netsim_nodes.side_effect in mock_add_error.mock_calls))

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.partial")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.toggle_ftpes_on_nodes")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.generate_node_batches")
    def test_toggle_ftpes__is_successful(self, mock_node_batches, mock_toggle_ftpes, mock_partial,
                                         mock_picklable_boundmethod, mock_debug_log, *_):
        with patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow."
                   "get_nodes_ftpes_status") as mock_get_node_ftpes_status:
            mock_node_batches.return_value = [self.nodes_list[:2], self.nodes_list[2:]]
            self.flow.toggle_ftpes(self.nodes_list)
            self.assertTrue(mock_node_batches.called)
            self.assertEqual(5, mock_debug_log.call_count)
            mock_toggle_ftpes.assert_called_with(mock_node_batches.return_value[1], "activate")
            mock_picklable_boundmethod.assert_called(mock_toggle_ftpes)
            mock_partial.assert_called_with(mock_picklable_boundmethod.return_value,
                                            mock_node_batches.return_value[1], "deactivate")
            mock_get_node_ftpes_status.assert_called_with(mock_node_batches.return_value[1], "activate")

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.picklable_boundmethod")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.partial")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.toggle_ftpes_on_nodes")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.generate_node_batches")
    def test_toggle_ftpes__raises_exception_while_calling_generate_node_batches(
            self, mock_node_batches, mock_toggle_ftpes, mock_partial, mock_picklable_boundmethod, mock_debug_log, *_):
        with patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow."
                   "get_nodes_ftpes_status") as mock_get_node_ftpes_status:
            with patch('enmutils_int.lib.profile.TeardownList.append') as mock_teardown_append:

                mock_node_batches.side_effect = Exception("something is wrong")
                self.assertFalse(mock_node_batches.called)
                self.assertEqual(0, mock_debug_log.call_count)
                self.assertFalse(mock_toggle_ftpes.called)
                self.assertFalse(mock_get_node_ftpes_status.called)
                self.assertFalse(mock_picklable_boundmethod.called)
                self.assertFalse(mock_partial.called)
                self.assertFalse(mock_teardown_append.called)
                self.assertRaises(EnvironError, self.flow.toggle_ftpes, self.nodes_list)

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.get_current_job_status")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    def test_toggle_ftpes_on_nodes__if_ftpes_activated_successfully(self, mock_add_error, mock_log_debug,
                                                                    mock_get_current_job_status):

        response = self.flow.user.enm_execute.return_value
        response.get_output.return_value = ["Successfully started a job for FTPES activate operation. "
                                            "'secadm job get -j abc' to get progress info."]
        self.flow.toggle_ftpes_on_nodes(self.nodes_list, "activate")
        self.assertEqual(4, mock_log_debug.call_count)
        self.assertFalse(mock_add_error.called)
        mock_get_current_job_status.assert_called_with("secadm job get -j abc")

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.get_current_job_status")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    def test_toggle_ftpes_on_nodes__raises_enm_application_error_while_activating_ftpes(self, mock_add_error,
                                                                                        mock_log_debug,
                                                                                        mock_get_current_job_status,
                                                                                        *_):
        response_output = (u'Error 10004 : The  NetworkElement specified does not exist '
                           u'Suggested Solution : Please specify a valid NetworkElement '
                           u'that exists in the system.')
        response = self.flow.user.enm_execute.return_value
        response.get_output.side_effect = [response_output]
        self.flow.toggle_ftpes_on_nodes(self.nodes_list, "activate")
        self.assertEqual(1, mock_log_debug.call_count)
        message = "Cannot activate the FTPES on 2 nodes due to {0}".format(response_output)
        self.assertTrue(call(EnmApplicationError(message) in mock_add_error.mock_calls))
        self.assertFalse(mock_get_current_job_status.called)

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.get_current_job_status")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    def test_toggle_ftpes_on_nodes__if_ftpes_deactivated_successfully(
            self, mock_add_error, mock_log_debug, mock_get_current_job_status):
        response = self.flow.user.enm_execute.return_value
        response.get_output.return_value = ["Successfully started a job for FTPES deactivate operation. "
                                            "'secadm job get -j abc' to get progress info."]
        self.flow.toggle_ftpes_on_nodes(self.nodes_list, "deactivate")
        self.assertEqual(3, mock_log_debug.call_count)
        self.assertFalse(mock_add_error.called)
        self.assertFalse(mock_get_current_job_status.called)

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.get_current_job_status")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    def test_toggle_ftpes_on_nodes__raises_enm_application_error_while_deactivating_ftpes(self, mock_add_error,
                                                                                          mock_log_debug,
                                                                                          mock_get_current_job_status):
        response_output = (u'Error 10004 : The  NetworkElement specified does not exist '
                           u'Suggested Solution : Please specify a valid NetworkElement '
                           u'that exists in the system.')
        response = self.flow.user.enm_execute.return_value
        response.get_output.side_effect = [response_output]
        self.flow.toggle_ftpes_on_nodes(self.nodes_list, "deactivate")
        self.assertEqual(1, mock_log_debug.call_count)
        message = "Cannot activate the FTPES on 2 nodes due to {0}".format(response_output)
        self.assertTrue(call(EnmApplicationError(message) in mock_add_error.mock_calls))
        self.assertFalse(mock_get_current_job_status.called)

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.get_current_job_status")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    def test_toggle_ftpes_on_nodes__raises_exception_if_no_nodes(self, mock_add_error, mock_get_current_job_status,
                                                                 mock_log_debug, *_):
        self.flow.user.enm_execute.return_value = Exception
        self.flow.toggle_ftpes_on_nodes([], "some_string")
        self.assertFalse(mock_get_current_job_status.called)
        self.assertTrue(mock_log_debug.called)
        self.assertTrue(call(EnvironError(self.flow.user.enm_execute.return_value) in mock_add_error.mock_calls))

    # get_current_job_status test casess
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    @patch('enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    def test_get_current_job_status__if_job_status_is_not_completed(self, mock_log_debug, *_):
        response = self.flow.user.enm_execute.return_value
        response.get_output.return_value = [u'Job Id\tCommand Id\tJob User\tJob Status\tJob Start Date\tJob End Date',
                                            u'abc\tFTPES_ACTIVATE\tFTPES_01\tPENDING\tN/A\tN/A',
                                            u'\t\t\t\t\t\tLTE31dg2ERBS00039\tPENDING\tN/A\tN/A\tN/A\tN/A']
        self.assertRaises(EnvironError, self.flow.get_current_job_status, Mock())
        self.assertTrue(mock_log_debug.called)

    @patch('enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    def test_get_current_job_status__if_status_is_completed(self, mock_add_error, mock_log_debug, *_):
        response = self.flow.user.enm_execute.return_value
        response.get_output.return_value = [u'Job  Id\tCommand Id\tJob User\tJob Status\tJob Start Date\tJob End Date',
                                            u'abc\tFTPES_ACTIVATE\tFTPES_01\tCOMPLETED\tN/A\tN/A',
                                            u'\t\t\t\t\t\tLTE31dg2ERBS00039\tCOMPLETED\tN/A\tN/A\tN/A\tN/A']
        self.flow.get_current_job_status(Mock())
        self.assertTrue(mock_log_debug.called)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    def test_get_current_job_status__if_status_running(self, mock_add_error, mock_log_debug, *_):
        response = self.flow.user.enm_execute.return_value
        response.get_output.return_value = [u'Job Id\tCommand Id\tJob User\tJob Status\tJob Start Date\tJob End Date',
                                            u'abc\tFTPES_ACTIVATING\tFTPES_01\tRUNNING\tN/A\tN/A',
                                            u'\t\t\t\t\t\tLTE31dg2ERBS00039\tRUNNING\tN/A\tN/A\tN/A\tN/A']
        self.assertRaises(EnvironError, self.flow.get_current_job_status, Mock())
        self.assertTrue(mock_log_debug.called)
        self.assertFalse(mock_add_error.called)

    @patch('enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.time.sleep', return_value=0)
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    def test_get_current_job_status__raises_exception(self, mock_add_error, mock_log_debug, *_):
        self.flow.user.enm_execute.return_value = Exception
        self.flow.get_current_job_status(Mock())
        self.assertTrue(mock_log_debug.called)
        self.assertTrue(call(EnvironError(self.flow.user.enm_execute.return_value) in mock_add_error.mock_calls))

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.check_ldap_is_configured_on_nodes")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.get_synchronised_nodes")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.get_required_nodes")
    def tests_ftpes_profile_prerequisites__is_successful(self, mock_get_required_nodes, mock_debug, mock_sync_nodes,
                                                         mock_ldap_config_nodes, mock_update_nodes_list):
        mock_get_required_nodes.return_value = self.nodes_list
        mock_sync_nodes.return_value = self.nodes_list[:3]
        mock_ldap_config_nodes.return_value = self.nodes_list[:2]
        self.flow.ftpes_profile_prerequisites(self.nodes_list)
        self.assertTrue(mock_get_required_nodes.called)
        self.assertTrue(mock_sync_nodes.called)
        self.assertTrue(mock_ldap_config_nodes.called)
        self.assertTrue(mock_debug.called)
        self.assertTrue(mock_update_nodes_list.called)

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.check_ldap_is_configured_on_nodes")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.get_synchronised_nodes")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.get_required_nodes")
    def tests_ftpes_profile_prerequisites__raises_env_error_if_synced_nodes_not_available(self, mock_get_required_nodes,
                                                                                          mock_debug, mock_sync_nodes,
                                                                                          mock_ldap_config_nodes,
                                                                                          mock_update_nodes):
        mock_sync_nodes.return_value = []
        self.assertRaises(EnvironError, self.flow.ftpes_profile_prerequisites, self.nodes_list)
        self.assertFalse(mock_get_required_nodes.called)
        self.assertTrue(mock_sync_nodes.called)
        self.assertFalse(mock_ldap_config_nodes.called)
        self.assertTrue(mock_debug.called)
        self.assertFalse(mock_update_nodes.called)

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.check_ldap_is_configured_on_nodes")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.get_synchronised_nodes")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.get_required_nodes")
    def tests_ftpes_profile_prerequisites__raises_env_error_if_ldap_configured_nodes_not_available(
            self, mock_get_required_nodes, mock_debug, mock_sync_nodes, mock_ldap_config_nodes, mock_update_nodes):
        mock_sync_nodes.return_value = self.nodes_list
        mock_ldap_config_nodes.return_value = []
        self.assertRaises(EnvironError, self.flow.ftpes_profile_prerequisites, self.nodes_list)
        self.assertFalse(mock_get_required_nodes.called)
        self.assertTrue(mock_sync_nodes.called)
        self.assertTrue(mock_ldap_config_nodes.called)
        self.assertTrue(mock_debug.called)
        self.assertFalse(mock_update_nodes.called)

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.group_nodes_per_netsim_host")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    def tests_get_required_nodes__is_successful(self, mock_debug, mock_group_nodes_per_netsim_host, mock_add_error):
        mock_group_nodes_per_netsim_host.return_value = self.netsims_with_nodes
        self.flow.get_required_nodes(self.nodes_list, self.flow.NETWORK_PERCENT)
        self.assertTrue(mock_group_nodes_per_netsim_host.called)
        self.assertFalse(mock_add_error.called)
        self.assertTrue(mock_debug.called)

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.get_success_and_failed_node_ftpes_status")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    def test_get_nodes_ftpes_status__if_ftpes_activated_successfully(self, mock_add_error, mock_log_debug, *_):
        response = self.flow.user.enm_execute.return_value
        response.get_output.return_value = [u'FDN : NetworkElement=123,ComConnectivityInformation=1',
                                            u'fileTransferProtocol :  FTPES', u'',
                                            u'FDN : NetworkElement=132,ComConnectivityInformation=1',
                                            u'fileTransferProtocol :  FTPES', u'', u'', u'2  instance(s)']
        self.flow.get_nodes_ftpes_status(self.nodes_list, "activate")
        self.assertEqual(mock_log_debug.call_count, 1)
        self.assertFalse(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.get_success_and_failed_node_ftpes_status")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    def test_get_nodes_ftpes_status_raises_enm_application_error_while_getting_ftpes_status(self, mock_add_error,
                                                                                            mock_log_debug, *_):
        response_output = (u'Error 10004 : The NetworkElement specified does not exist '
                           u'Suggested Solution : Please specify a valid NetworkElement '
                           u'that exists in the system.')
        response = self.flow.user.enm_execute.return_value
        response.get_output.side_effect = [response_output]
        self.flow.get_nodes_ftpes_status(self.nodes_list, "activate")
        self.assertEqual(mock_log_debug.call_count, 1)
        message = "Error occurred while getting FTPES status for 2 nodes due to {0}".format(response_output)
        self.assertTrue(call(EnmApplicationError(message) in mock_add_error.mock_calls))

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.get_success_and_failed_node_ftpes_status")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    def test_get_nodes_ftpes_status__if_getting_empty_ftpes_status(self, mock_add_error, mock_log_debug, *_):
        response = self.flow.user.enm_execute.return_value
        response.get_output.return_value = [u'', u'0 instance(s)']
        self.flow.get_nodes_ftpes_status(self.nodes_list, "activate")
        self.assertEqual(mock_log_debug.call_count, 1)
        self.assertFalse(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.get_success_and_failed_node_ftpes_status")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    def test_get_nodes_ftpes_status__if_getting_empty_response(self, mock_add_error, mock_log_debug, *_):
        response = self.flow.user.enm_execute.return_value
        response.get_output.return_value = []
        self.flow.get_nodes_ftpes_status(self.nodes_list, "activate")
        self.assertEqual(mock_log_debug.call_count, 1)
        self.assertFalse(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    def test_get_nodes_ftpes_status__if_activation_failed_raises_error(self, mock_add_error, mock_log_debug, *_):
        response = self.flow.user.enm_execute.return_value
        response.get_output.return_value = [u'Error 10004 : The NetworkElement specified does not exist '
                                            u'Suggested Solution : Please specify a valid NetworkElement '
                                            u'that exists in the system.']
        self.flow.get_nodes_ftpes_status(self.nodes_list, "activate")
        self.assertEqual(mock_add_error.call_count, 1)
        self.assertEqual(mock_log_debug.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    def test_get_success_and_failed_node_ftpes_status__if_status_is_activate(self, *_):
        response = self.flow.user.enm_execute.return_value
        enm_output = response.get_output.return_value = [u'FDN : NetworkElement=123,ComConnectivityInformation=1',
                                                         u'fileTransferProtocol   : FTPES', u'',
                                                         u'FDN : NetworkElement=132,ComConnectivityInformation=1',
                                                         u'fileTransferProtocol   : FTPES', u'', u'', u'2 instance(s)']
        self.flow.get_success_and_failed_node_ftpes_status("activate", enm_output, self.nodes_list[:2])

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    def test_get_success_and_failed_node_ftpes_status__if_status_is_deactivate(self, mock_add_error):
        response = self.flow.user.enm_execute.return_value
        enm_output = response.get_output.return_value = [u'FDN : NetworkElement=1234,ComConnectivityInformation=1',
                                                         u'fileTransferProtocol  : FTPES', u'',
                                                         u'FDN : NetworkElement=1325,ComConnectivityInformation=1',
                                                         u'fileTransferProtocol  : FTPES', u'', u'', u'2  instance(s)']
        self.flow.get_success_and_failed_node_ftpes_status("deactivate", enm_output, self.nodes_list)
        self.assertTrue(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.add_error_as_exception")
    def test_get_success_and_failed_node_ftpes_status__raises_error(self, mock_add_error):
        response = self.flow.user.enm_execute.return_value
        enm_output = response.get_output.return_value = [u'FDN : NetworkElement=1236,ComConnectivityInformation=1',
                                                         u'fileTransferProtocol : FTPES', u'',
                                                         u'FDN : NetworkElement=1328,ComConnectivityInformation=1',
                                                         u'fileTransferProtocol : FTPES', u'', u'', u'2 instance(s)']
        self.flow.get_success_and_failed_node_ftpes_status("activate", enm_output, self.nodes_list)
        self.assertTrue(mock_add_error.called)

    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.Ftpes01Flow.get_node_error_state", return_value=['ERROR'])
    @patch("enmutils_int.lib.profile_flows.ftpes_flows.ftpes_flow.log.logger.debug")
    def test_check_any_nodes_in_error_state_succcessful(self, mock_log_debug, *_):
        response = self.flow.user.enm_execute.return_value
        response.get_output.return_value = [u'\t\t\t\t\t\tLTE07dg2ERBS00064\tERROR\t2023-05-29 06:56:06\t00:00:44.156\t'
                                            u'[Check trustInstall: already installed][Perform action: '
                                            u'startOnlineEnrollment performed.'
                                            u'Polling progress][Check action failed] [FAILURE]\tN/A']
        self.flow.check_any_nodes_in_error_state(Mock())
        self.assertTrue(mock_log_debug.called)

if __name__ == "__main__":
    unittest2.main(verbosity=2)
