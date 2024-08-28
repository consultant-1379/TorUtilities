#!/usr/bin/env python
import unittest2
from enmutils.lib.enm_user_2 import User
from enmutils.lib.exceptions import EnmApplicationError, EnvironError
from enmutils_int.lib.profile_flows.pm_flows import pm79profile
from enmutils_int.lib.workload import pm_79
from mock import patch, PropertyMock, Mock, call
from testslib import unit_test_utils


class Pm79ProfileUnitTests(unittest2.TestCase):

    def setUp(self):
        unit_test_utils.setup()
        self.user = Mock(spec_set=User(username="test"))
        self.pm_79 = pm_79.PM_79()
        self.profile = pm79profile.Pm79Profile()
        self.profile.NAME = "PM_79"
        self.profile.USER = Mock()
        self.profile.USER_ROLES = ['Cmedit_Administrator', 'PM_Operator']
        self.profile.NUM_NODES = {'RadioNode': -1, 'ERBS': -1}
        self.profile.TOTAL_REQUIRED_NODES = 3
        self.profile.SCHEDULED_TIMES_STRINGS = ["08:00:00", "12:00:00"]

    def tearDown(self):
        unit_test_utils.tear_down()

    @staticmethod
    def get_nodes(node_type, number_of_nodes):
        return [Mock(primary_type=node_type,
                     node_id="id{0}".format(node_type + str(_))) for _ in range(number_of_nodes)]

    def get_selected_nodes(self):
        radionode_nodes = self.get_nodes("RadioNode", 3)
        erbs_nodes = self.get_nodes("ERBS", 1)
        rbs_nodes = self.get_nodes("RBS", 1)
        radionode0_name = radionode_nodes[0].node_id
        radionode2_name = radionode_nodes[2].node_id
        erbs_name = erbs_nodes[0].node_id
        rbs_name = rbs_nodes[0].node_id

        selected_nodes = [
            {radionode0_name:
             {'node': radionode_nodes[0],
              'node_rfport_fdn_list': 'ManagedElement={0},Equipment=1,FieldReplaceableUnit=1,RfPort=A'.format(radionode0_name),
              'ulsa_mo_list': ['ManagedElement={0},NodeSupport=1,ULSA=1'.format(radionode0_name)]}},
            {radionode2_name:
             {'node': radionode_nodes[2],
              'node_rfport_fdn_list': 'ManagedElement={0},Equipment=1,FieldReplaceableUnit=1,RfPort=A'.format(radionode2_name),
              'ulsa_mo_list': ['ManagedElement={0},NodeSupport=1,ULSA=1'.format(radionode2_name)]}},
            {erbs_name:
             {'node': erbs_nodes[0],
              'node_rfport_fdn_list': 'SubNetwork=1,MeContext={0},ManagedElement=1,Equipment=1,AuxPlugInUnit=1, '
                                      'DeviceGroup=1,RfPort=1'.format(erbs_name),
              'ulsa_mo_list': ['SubNetwork=1,MeContext={0},ManagedElement=1,NodeManagementFunction=1,'
                               'ULSA=1'.format(erbs_name),
                               'SubNetwork=1,MeContext={0},ManagedElement=1,NodeManagementFunction=1,'
                               'ULSA=PM_79_ULSA_1'.format(erbs_name),
                               'SubNetwork=1,MeContext={0},ManagedElement=1,NodeManagementFunction=1,'
                               'ULSA=PM_79_ULSA_2'.format(erbs_name),
                               'SubNetwork=1,MeContext={0},ManagedElement=1,NodeManagementFunction=1,'
                               'ULSA=PM_79_ULSA_3'.format(erbs_name)]}},
            {rbs_name: {'node': rbs_nodes[0],
                        'rfport_ldn': 'SubNetwork=1,MeContext={0},ManagedElement=1,Equipment=1,AuxPlugInUnit=1,'
                                      'DeviceGroup=1,RfPort=1'.format(rbs_name),
                        'ulsa_mo_list': ['SubNetwork=1,MeContext={0},ManagedElement=1,NodeManagementFunction=1, '
                                         'ULSA=1'.format(rbs_name),
                                         'SubNetwork=1,MeContext={0},ManagedElement=1,NodeManagementFunction=1,'
                                         'ULSA=PM_79_ULSA_1'.format(rbs_name),
                                         'SubNetwork=1,MeContext={0},ManagedElement=1,NodeManagementFunction=1,'
                                         'ULSA=PM_79_ULSA_2'.format(rbs_name),
                                         'SubNetwork=1,MeContext={0},ManagedElement=1,NodeManagementFunction=1,'
                                         'ULSA=PM_79_ULSA_3'.format(rbs_name)]}}]
        return selected_nodes

    @patch("time.sleep")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.ThreadQueue")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.show_errored_threads")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.start_ulsa_uplink_measurement")
    def test_create_and_execute_threads_ulsa__is_successful(
            self, mock_start_ulsa_measurements, mock_show_errored_threads, mock_thread_queue, _):
        self.profile.USER = self.user
        selected_nodes = {"ERBS": {}, "RadioNode": {}, "RBS": {}}
        node_info = []
        for i in xrange(4):
            node_type = "ERBS" if i < 1 else "RadioNode"
            node_info.append({"node": Mock(), "node_rfport_fdn_list": "rfport_ldn_blah", "ulsa_mo_list": ["ulsa_mo_blah"]})
            selected_nodes[node_type]["node{0}".format(i)] = node_info[i]

        selected_nodes_per_type = [{"node0": node_info[0]}, {"node1": node_info[1]},
                                   {"node3": node_info[3]}, {"node2": node_info[2]}]
        self.profile.create_and_execute_threads_ulsa(selected_nodes)
        mock_thread_queue.assert_called_with(selected_nodes_per_type, len(selected_nodes_per_type),
                                             func_ref=mock_start_ulsa_measurements,
                                             args=[self.user])
        self.assertTrue(mock_show_errored_threads.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.wait_until_first_scheduled_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.create_and_execute_threads_ulsa")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.keep_running")
    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.initialize_profile_prerequisites")
    def test_execute_flow__is_successful_with_one_iteration(
            self, mock_initialize_profile_prerequisites, mock_teardown_append, mock_keep_running,
            mock_create_and_execute_threads_ulsa, mock_add_exception, *_):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile."
                   "check_and_remove_old_ulsas_in_enm") as mock_check_and_remove_old_ulsas_in_enm:
            selected_nodes = self.get_selected_nodes()
            mock_initialize_profile_prerequisites.return_value = selected_nodes
            mock_keep_running.side_effect = [True, False]

            self.profile.execute_flow()

            self.assertEqual(mock_teardown_append.call_count, 1)
            self.assertEqual(mock_keep_running.call_count, 2)
            self.assertEqual(mock_create_and_execute_threads_ulsa.call_count, 1)
            self.assertFalse(mock_add_exception.called)
            mock_create_and_execute_threads_ulsa.assert_called_with(selected_nodes)
            mock_check_and_remove_old_ulsas_in_enm.assert_called_with(self.profile.USER, self.profile)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.wait_until_first_scheduled_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.create_and_execute_threads_ulsa")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.keep_running")
    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.initialize_profile_prerequisites")
    def test_execute_flow__is_successful_with_two_iterations(
            self, mock_initialize_profile_prerequisites, mock_teardown_append, mock_keep_running,
            mock_create_and_execute_threads_ulsa, mock_add_exception, *_):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile."
                   "check_and_remove_old_ulsas_in_enm") as mock_check_and_remove_old_ulsas_in_enm:
            selected_nodes = self.get_selected_nodes()
            mock_initialize_profile_prerequisites.return_value = selected_nodes
            mock_keep_running.side_effect = [True, True, False]
            self.profile.execute_flow()

            self.assertEqual(mock_teardown_append.call_count, 1)
            self.assertEqual(mock_keep_running.call_count, 3)
            self.assertEqual(mock_create_and_execute_threads_ulsa.call_count, 2)
            self.assertFalse(mock_add_exception.called)
            mock_create_and_execute_threads_ulsa.assert_called_with(selected_nodes)
            mock_check_and_remove_old_ulsas_in_enm.assert_called_with(self.profile.USER, self.profile)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.wait_until_first_scheduled_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.create_and_execute_threads_ulsa")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.keep_running")
    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.initialize_profile_prerequisites")
    def test_execute_flow__adds_error_if_no_nodes_selected(
            self, mock_initialize_profile_prerequisites, mock_teardown_append, mock_keep_running,
            mock_create_and_execute_threads_ulsa, mock_add_exception, *_):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile."
                   "check_and_remove_old_ulsas_in_enm") as mock_check_and_remove_old_ulsas_in_enm:
            mock_initialize_profile_prerequisites.return_value = {}
            self.profile.execute_flow()

            self.assertFalse(mock_teardown_append.called)
            self.assertFalse(mock_keep_running.called)
            self.assertFalse(mock_create_and_execute_threads_ulsa.called)
            self.assertEqual(mock_add_exception.call_count, 1)
            self.assertFalse(mock_check_and_remove_old_ulsas_in_enm.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.wait_until_first_scheduled_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.create_and_execute_threads_ulsa")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.keep_running")
    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.initialize_profile_prerequisites")
    def test_execute_flow__adds_error_if_exception_thrown_trying_to_create_and_execute_threads_ulsa(
            self, mock_initialize_profile_prerequisites, mock_teardown_append, mock_keep_running,
            mock_create_and_execute_threads_ulsa, mock_add_exception, *_):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile."
                   "check_and_remove_old_ulsas_in_enm") as mock_check_and_remove_old_ulsas_in_enm:
            selected_nodes = self.get_selected_nodes()
            mock_initialize_profile_prerequisites.return_value = selected_nodes
            mock_create_and_execute_threads_ulsa.side_effect = Exception
            mock_keep_running.side_effect = [True, False]
            self.profile.execute_flow()

            self.assertEqual(mock_teardown_append.call_count, 1)
            self.assertEqual(mock_keep_running.call_count, 2)
            self.assertEqual(mock_create_and_execute_threads_ulsa.call_count, 1)
            self.assertEqual(mock_add_exception.call_count, 1)
            mock_create_and_execute_threads_ulsa.assert_called_with(selected_nodes)
            mock_check_and_remove_old_ulsas_in_enm.assert_called_with(self.profile.USER, self.profile)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.state", new_callable=PropertyMock)
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.wait_until_first_scheduled_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.sleep_until_time")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.create_and_execute_threads_ulsa")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.keep_running")
    @patch("enmutils_int.lib.profile.TeardownList.append")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.initialize_profile_prerequisites")
    def test_execute_flow__add_error_if_check_and_remove_old_ulsas_in_enm_raises_enm_application_error(
            self, mock_initialize_profile_prerequisites, mock_teardown_append, mock_keep_running,
            mock_create_and_execute_threads_ulsa, mock_add_exception, *_):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile."
                   "check_and_remove_old_ulsas_in_enm") as mock_check_and_remove_old_ulsas_in_enm:
            selected_nodes = self.get_selected_nodes()
            mock_initialize_profile_prerequisites.return_value = selected_nodes
            mock_keep_running.side_effect = [True, True, False]
            mock_check_and_remove_old_ulsas_in_enm.side_effect = EnmApplicationError("ENM command execution "
                                                                                     "unsuccessful")
            self.profile.execute_flow()
            self.assertEqual(mock_teardown_append.call_count, 1)
            self.assertEqual(mock_keep_running.call_count, 3)
            self.assertEqual(mock_create_and_execute_threads_ulsa.call_count, 2)
            mock_create_and_execute_threads_ulsa.assert_called_with(selected_nodes)
            self.assertTrue(call(mock_check_and_remove_old_ulsas_in_enm.side_effect in mock_add_exception.mock_calls))

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.raise_for_status")
    def test_start_ulsa_uplink_measurement__is_successful(
            self, mock_raise_for_status):
        node_info = self.get_selected_nodes()[2]  # ERBS node with 4 ULSA ID's

        response = Mock()
        response.content = '{"filepath":"","triggeredat":"Tue, 28 Aug 2018 11:09:21 +0100"}'
        self.user.post.return_value = response

        pm79profile.start_ulsa_uplink_measurement(node_info, self.user)
        self.assertEqual(mock_raise_for_status.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.raise_for_status")
    def test_start_ulsa_uplink_measurement__raises_error_if_response_from_enm_is_unexpected(
            self, mock_raise_for_status):
        node_info = self.get_selected_nodes()[2]  # ERBS node with 4 ULSA ID's

        response = Mock()
        response.content = 'blah'
        self.user.post.return_value = response

        self.assertRaises(EnmApplicationError, pm79profile.start_ulsa_uplink_measurement, node_info, self.user)
        self.assertEqual(mock_raise_for_status.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.raise_for_status")
    def test_stop_ulsa_uplink_measurement__is_successful(self, mock_raise_for_status):
        node_info = self.get_selected_nodes()[2]  # ERBS node with 1 ULSA ID

        response = Mock()
        response.content = '{"jobState":"STOPPED","endTime":1555416720742,"poId":"281475013683876"}'
        self.user.put.return_value = response

        pm79profile.stop_ulsa_uplink_measurement(node_info, self.user)
        self.assertEqual(mock_raise_for_status.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.raise_for_status")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm79profile.log.logger.debug')
    def test_stop_ulsa_uplink_measurement__raises_enm_application_error(self, mock_log, *_):
        node_info = self.get_selected_nodes()[0]
        response = Mock()
        response.content = 'blah'
        self.user.put.return_value = response
        self.assertRaises(EnmApplicationError, pm79profile.stop_ulsa_uplink_measurement, node_info, self.user)
        self.assertEqual(mock_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.raise_for_status")
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm79profile.log.logger.debug')
    def test_stop_ulsa_uplink_measurement__raises_exception(self, mock_log, *_):
        node_info = self.get_selected_nodes()[0]
        response = Mock(status_code=500, ok=False)
        self.user.put.return_value = response
        self.assertRaises(EnmApplicationError, pm79profile.stop_ulsa_uplink_measurement, node_info, self.user)
        self.assertEqual(mock_log.call_count, 3)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.stop_ulsa_uplink_measurement")
    def test_perform_teardown_actions__is_successful(
            self, mock_stop_ulsa_uplink_measurement):
        selected_nodes_per_type = self.get_selected_nodes()

        selected_nodes = {"RadioNode": dict(selected_nodes_per_type[0].items() + selected_nodes_per_type[1].items()),
                          "ERBS": dict(selected_nodes_per_type[2]), "RBS": dict(selected_nodes_per_type[3])}

        pm79profile.perform_teardown_actions(self.user, selected_nodes)
        self.assertEqual(mock_stop_ulsa_uplink_measurement.call_count, 4)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.create_users")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.select_nodes_to_use")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.add_error_as_exception")
    def test_initialize_profile_prerequisites__is_successful(
            self, mock_add_exception, mock_nodes_list, mock_select_nodes_to_use, mock_create_users):
        mock_nodes_list.return_value = [Mock(), Mock()]
        self.profile.initialize_profile_prerequisites()
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_select_nodes_to_use.called)
        self.assertFalse(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.create_users")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.select_nodes_to_use")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.add_error_as_exception")
    def test_initialize_profile_prerequisites__returns_none_if_no_nodes_in_node_list(
            self, mock_add_exception, mock_nodes_list, mock_select_nodes_to_use, mock_create_users):
        mock_nodes_list.return_value = []
        self.assertEqual(self.profile.initialize_profile_prerequisites(), None)
        self.assertFalse(mock_create_users.called)
        self.assertFalse(mock_select_nodes_to_use.called)
        self.assertFalse(mock_add_exception.called)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.create_users")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.select_nodes_to_use")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.add_error_as_exception")
    def test_initialize_profile_prerequisites__adds_error_if_cannot_create_user(
            self, mock_add_exception, mock_nodes_list, mock_select_nodes_to_use, mock_create_users):
        mock_nodes_list.return_value = [Mock(), Mock()]
        mock_create_users.side_effect = Exception
        self.profile.initialize_profile_prerequisites()
        self.assertTrue(mock_create_users.called)
        self.assertFalse(mock_select_nodes_to_use.called)
        self.assertEqual(mock_add_exception.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.create_users")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.select_nodes_to_use")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.add_error_as_exception")
    def test_initialize_profile_prerequisites__adds_error_if_select_nodes_to_use_throws_exception(
            self, mock_add_exception, mock_nodes_list, mock_select_nodes_to_use, mock_create_users):
        mock_nodes_list.return_value = [Mock(), Mock()]
        mock_select_nodes_to_use.side_effect = Exception
        self.profile.initialize_profile_prerequisites()
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_select_nodes_to_use.called)
        self.assertEqual(mock_add_exception.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.create_users")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.select_nodes_to_use")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.get_nodes_list_by_attribute")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.add_error_as_exception")
    def test_initialize_profile_prerequisites__adds_error_if_select_nodes_to_use_throws_keyerror(
            self, mock_add_exception, mock_nodes_list, mock_select_nodes_to_use, mock_create_users):
        mock_nodes_list.return_value = [Mock(), Mock()]
        mock_select_nodes_to_use.side_effect = KeyError
        self.profile.initialize_profile_prerequisites()
        self.assertTrue(mock_create_users.called)
        self.assertTrue(mock_select_nodes_to_use.called)
        self.assertEqual(mock_add_exception.call_count, 1)

    # select_nodes_to_use test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "get_required_nodes_from_profile_selected_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.get_rfport_fdn_list_from_profile_allocated_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "select_nodes_from_pool_that_contain_rfport_mo")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.get_synchronised_nodes")
    def test_select_nodes_to_use__returns_nodes_successfully(self, mock_get_synchronised_nodes,
                                                             mock_select_nodes_from_pool_that_contain_rfport_mo,
                                                             mock_get_rfport_fdn_list_from_profile_alctd_nodes,
                                                             mock_update_profile_persistence_nodes_list,
                                                             mock_debug_log, mock_get_req_nodes):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile."
                   "group_nodes_per_ne_type") as mock_group_nodes_per_ne_type:
            erbs_nodes = self.get_nodes("ERBS", 4)
            radionode_nodes = self.get_nodes("RadioNode", 2)
            mock_group_nodes_per_ne_type.return_value = {"ERBS": erbs_nodes, "RadioNode": radionode_nodes}
            allocated_nodes = erbs_nodes + radionode_nodes
            erbs_nodes[0].node_id = "LTE98dg2ERBS00001"
            radionode_nodes[0].node_id = "LTE03DG200003"
            mock_get_synchronised_nodes.return_value = [erbs_nodes[0], radionode_nodes[0]]
            rfort_fdn_list = [u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE98ERBS00001,'
                              u'Equipment=1,FieldReplaceableUnit=1,RfPort=1',
                              u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE03DG200003,'
                              u'Equipment=1,FieldReplaceableUnit=1,RfPort=1']
            mock_get_rfport_fdn_list_from_profile_alctd_nodes.return_value = rfort_fdn_list

            erbs_nodes_that_contain_rfport_mos = {erbs_nodes[0].node_id: {"node": erbs_nodes[0],
                                                                          "rfport": rfort_fdn_list[0]}}
            radionode_nodes_that_contain_rfport_mos = {radionode_nodes[0].node_id: {"node": radionode_nodes[0],
                                                                                    "rfport": rfort_fdn_list[1]}}
            mock_select_nodes_from_pool_that_contain_rfport_mo.side_effect = [radionode_nodes_that_contain_rfport_mos,
                                                                              erbs_nodes_that_contain_rfport_mos]
            nodes_with_ulsa_mos = {"ERBS": erbs_nodes_that_contain_rfport_mos,
                                   "RadioNode": radionode_nodes_that_contain_rfport_mos}
            mock_get_req_nodes.return_value = nodes_with_ulsa_mos, allocated_nodes
            self.assertEqual(nodes_with_ulsa_mos, self.profile.select_nodes_to_use(self.user, allocated_nodes))
            self.assertTrue(mock_get_synchronised_nodes.called)
            self.assertTrue(mock_select_nodes_from_pool_that_contain_rfport_mo.called)
            self.assertTrue(mock_get_rfport_fdn_list_from_profile_alctd_nodes.called)
            self.assertEqual(mock_update_profile_persistence_nodes_list.call_count, 1)
            self.assertEqual(mock_debug_log.call_count, 5)
            self.assertEqual(mock_get_req_nodes.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.get_rfport_fdn_list_from_profile_allocated_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "select_nodes_from_pool_that_contain_rfport_mo")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.get_synchronised_nodes")
    def test_select_nodes_to_use__returns_none_if_no_synced_nodes(self, mock_get_synchronised_nodes,
                                                                  mock_select_nodes_from_pool_that_contain_rfport_mo,
                                                                  mock_get_rfport_fdn_list_from_profile_alctd_nodes,
                                                                  mock_update_profile_persistence_nodes_list,
                                                                  mock_add_error_as_exception, mock_debug_log):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
                   "get_required_nodes_from_profile_selected_nodes") as mock_get_req_nodes:
            with patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile."
                       "group_nodes_per_ne_type") as mock_group_nodes_per_ne_type:
                erbs_nodes = self.get_nodes("ERBS", 2)
                radio_nodes = self.get_nodes("RadioNode", 2)
                mock_group_nodes_per_ne_type.return_value = {"ERBS": erbs_nodes, "RadioNode": radio_nodes}
                allocated_nodes = erbs_nodes + radio_nodes
                mock_get_synchronised_nodes.return_value = []
                mock_get_rfport_fdn_list_from_profile_alctd_nodes.return_value = []

                erbs_nodes_that_contain_rfport_mos = {}
                radionode_nodes_that_contain_rfport_mos = {}
                mock_select_nodes_from_pool_that_contain_rfport_mo.side_effect = [radionode_nodes_that_contain_rfport_mos,
                                                                                  erbs_nodes_that_contain_rfport_mos]
                mock_get_req_nodes.return_value = {}, allocated_nodes
                self.assertEqual({}, self.profile.select_nodes_to_use(self.user, allocated_nodes))

                self.assertEqual(mock_add_error_as_exception.call_count, 2)
                self.assertTrue(mock_get_synchronised_nodes.called)
                self.assertTrue(mock_select_nodes_from_pool_that_contain_rfport_mo.called)
                self.assertTrue(mock_get_rfport_fdn_list_from_profile_alctd_nodes.called)
                self.assertEqual(mock_update_profile_persistence_nodes_list.call_count, 1)
                self.assertEqual(mock_debug_log.call_count, 5)
                self.assertEqual(mock_get_req_nodes.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.get_rfport_fdn_list_from_profile_allocated_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "select_nodes_from_pool_that_contain_rfport_mo")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.get_synchronised_nodes")
    def test_select_nodes_to_use__deallocate_unused_nodes_and_update_profile_persistence(
            self, mock_get_synchronised_nodes, mock_select_nodes_from_pool_that_contain_rfport_mo,
            mock_get_rfport_fdn_list_from_profile_alctd_nodes, mock_update_profile_persistence_nodes_list,
            mock_add_error_as_exception, mock_debug_log):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
                   "get_required_nodes_from_profile_selected_nodes") as mock_get_req_nodes:
            with patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile."
                       "group_nodes_per_ne_type") as mock_group_nodes_per_ne_type:
                erbs_nodes = self.get_nodes("ERBS", 2)
                radionode_nodes = self.get_nodes("RadioNode", 2)
                mock_group_nodes_per_ne_type.return_value = {"ERBS": erbs_nodes, "RadioNode": radionode_nodes}
                allocated_nodes = erbs_nodes + radionode_nodes
                erbs_nodes[0].node_id = "LTE98dg2ERBS00001"
                radionode_nodes[0].node_id = "LTE03DG200003"
                mock_get_synchronised_nodes.return_value = [erbs_nodes[0], radionode_nodes[0]]
                rfort_fdn_list = [u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE98ERBS00001,'
                                  u'Equipment=1,FieldReplaceableUnit=1,RfPort=1',
                                  u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE03DG200003,'
                                  u'Equipment=1,FieldReplaceableUnit=1,RfPort=1']
                mock_get_rfport_fdn_list_from_profile_alctd_nodes.return_value = rfort_fdn_list
                erbs_nodes_that_contain_rfport_mos = {erbs_nodes[0].node_id: {"node": erbs_nodes[0],
                                                                              "rfport": rfort_fdn_list[0]}}
                radionode_nodes_that_contain_rfport_mos = {radionode_nodes[0].node_id: {"node": radionode_nodes[0],
                                                                                        "rfport": rfort_fdn_list[1]}}
                mock_select_nodes_from_pool_that_contain_rfport_mo.side_effect = [radionode_nodes_that_contain_rfport_mos,
                                                                                  erbs_nodes_that_contain_rfport_mos]
                mock_get_req_nodes.return_value = ({'RadioNode': radionode_nodes_that_contain_rfport_mos,
                                                    'ERBS': erbs_nodes_that_contain_rfport_mos},
                                                   ['LTE03DG200003', 'LTE98dg2ERBS00001'])

                self.profile.select_nodes_to_use(self.user, allocated_nodes)
                self.assertEqual(mock_add_error_as_exception.call_count, 0)
                self.assertTrue(mock_get_synchronised_nodes.called)
                self.assertEqual(mock_select_nodes_from_pool_that_contain_rfport_mo.call_count, 2)
                self.assertTrue(mock_get_rfport_fdn_list_from_profile_alctd_nodes.called)
                self.assertEqual(mock_update_profile_persistence_nodes_list.call_count, 1)
                self.assertEqual(mock_debug_log.call_count, 5)
                self.assertEqual(mock_get_req_nodes.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.add_error_as_exception")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.get_rfport_fdn_list_from_profile_allocated_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "select_nodes_from_pool_that_contain_rfport_mo")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.get_synchronised_nodes")
    def test_select_nodes_to_use__if_unused_nodes_not_existed(
            self, mock_get_synchronised_nodes, mock_select_nodes_from_pool_that_contain_rfport_mo,
            mock_get_rfport_fdn_list_from_profile_alctd_nodes, mock_update_profile_persistence_nodes_list,
            mock_add_error_as_exception, mock_debug_log):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
                   "get_required_nodes_from_profile_selected_nodes") as mock_get_req_nodes:
            with patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile."
                       "group_nodes_per_ne_type") as mock_group_nodes_per_ne_type:
                erbs_nodes = self.get_nodes("ERBS", 2)
                radionode_nodes = self.get_nodes("RadioNode", 2)
                erbs_nodes[0].node_id = "LTE98dg2ERBS00001"
                erbs_nodes[1].node_id = "LTE98dg2ERBS00002"
                radionode_nodes[0].node_id = "LTE03DG200003"
                radionode_nodes[1].node_id = "LTE03DG200004"
                mock_group_nodes_per_ne_type.return_value = {"ERBS": erbs_nodes, "RadioNode": radionode_nodes}
                allocated_nodes = erbs_nodes + radionode_nodes

                mock_get_synchronised_nodes.return_value = erbs_nodes + erbs_nodes

                rfort_fdn_list = [u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE98ERBS00001,'
                                  u'Equipment=1,FieldReplaceableUnit=1,RfPort=1',
                                  u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE98ERBS00002,'
                                  u'Equipment=1,FieldReplaceableUnit=1,RfPort=1',
                                  u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE03DG200003,'
                                  u'Equipment=1,FieldReplaceableUnit=1,RfPort=1',
                                  u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE03DG200004,'
                                  u'Equipment=1,FieldReplaceableUnit=1,RfPort=1']
                mock_get_rfport_fdn_list_from_profile_alctd_nodes.return_value = rfort_fdn_list
                erbs_nodes_that_contain_rfport_mos = {erbs_nodes[0].node_id: {"node": erbs_nodes[0],
                                                                              "rfport": rfort_fdn_list[0]},
                                                      erbs_nodes[1].node_id: {"node": erbs_nodes[0],
                                                                              "rfport": rfort_fdn_list[1]}}
                radionode_nodes_that_contain_rfport_mos = {radionode_nodes[0].node_id: {"node": radionode_nodes[0],
                                                                                        "rfport": rfort_fdn_list[2]},
                                                           radionode_nodes[1].node_id: {"node": radionode_nodes[0],
                                                                                        "rfport": rfort_fdn_list[3]}}

                mock_select_nodes_from_pool_that_contain_rfport_mo.side_effect = [radionode_nodes_that_contain_rfport_mos,
                                                                                  erbs_nodes_that_contain_rfport_mos]
                mock_get_req_nodes.return_value = ({'RadioNode': radionode_nodes_that_contain_rfport_mos,
                                                    'EBRS': erbs_nodes_that_contain_rfport_mos},
                                                   ['LTE03DG200003', 'LTE03DG200004', 'LTE98dg2ERBS00002',
                                                    'LTE98dg2ERBS00001'])
                self.profile.select_nodes_to_use(self.user, allocated_nodes)
                self.assertEqual(mock_add_error_as_exception.call_count, 0)
                self.assertTrue(mock_get_synchronised_nodes.called)
                self.assertEqual(mock_select_nodes_from_pool_that_contain_rfport_mo.call_count, 2)
                self.assertTrue(mock_get_rfport_fdn_list_from_profile_alctd_nodes.called)
                self.assertEqual(mock_update_profile_persistence_nodes_list.call_count, 0)
                self.assertEqual(mock_debug_log.call_count, 4)
                self.assertEqual(mock_get_req_nodes.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "get_required_nodes_from_profile_selected_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "get_rfport_fdn_list_from_profile_allocated_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "select_nodes_from_pool_that_contain_rfport_mo")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.get_synchronised_nodes")
    def test_select_nodes_to_use__when_one_erbs_node_existed(self, mock_get_synchronised_nodes,
                                                             mock_select_nodes_from_pool_that_contain_rfport_mo,
                                                             mock_get_rfport_fdn_list_from_profile_alctd_nodes,
                                                             mock_update_profile_persistence_nodes_list,
                                                             mock_debug_log, mock_get_req_nodes):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile."
                   "group_nodes_per_ne_type") as mock_group_nodes_per_ne_type:
            erbs_nodes = self.get_nodes("ERBS", 1)
            radionode_nodes = self.get_nodes("RadioNode", 2)
            allocated_nodes = erbs_nodes + radionode_nodes
            erbs_nodes[0].node_id = "LTE98ERBS00001"
            radionode_nodes[0].node_id = "LTE03DG200003"
            radionode_nodes[1].node_id = "LTE03DG200004"
            mock_group_nodes_per_ne_type.return_value = {"ERBS": erbs_nodes, "RadioNode": radionode_nodes}
            mock_get_synchronised_nodes.return_value = [erbs_nodes[0], radionode_nodes[0], radionode_nodes[1]]
            rfort_fdn_list = [u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE98ERBS00001,'
                              u'Equipment=1,FieldReplaceableUnit=1,RfPort=1',
                              u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE03DG200003,'
                              u'Equipment=1,FieldReplaceableUnit=1,RfPort=1',
                              u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE03DG200004,'
                              u'Equipment=1,FieldReplaceableUnit=1,RfPort=1']
            mock_get_rfport_fdn_list_from_profile_alctd_nodes.return_value = rfort_fdn_list

            erbs_nodes_that_contain_rfport_mos = {erbs_nodes[0].node_id: {"node": erbs_nodes[0],
                                                                          "rfport": rfort_fdn_list[0]}}
            radionode_nodes_that_contain_rfport_mos = {radionode_nodes[0].node_id: {"node": radionode_nodes[0],
                                                                                    "rfport": rfort_fdn_list[1]},
                                                       radionode_nodes[1].node_id: {"node": radionode_nodes[1],
                                                                                    "rfport": rfort_fdn_list[2]}}
            mock_select_nodes_from_pool_that_contain_rfport_mo.side_effect = [radionode_nodes_that_contain_rfport_mos,
                                                                              erbs_nodes_that_contain_rfport_mos]
            nodes_with_ulsa_mos = {"ERBS": erbs_nodes_that_contain_rfport_mos,
                                   "RadioNode": radionode_nodes_that_contain_rfport_mos}
            mock_get_req_nodes.return_value = nodes_with_ulsa_mos, ['LTE03DG200003', 'LTE03DG200004', 'LTE98ERBS00001']
            self.assertEqual(nodes_with_ulsa_mos, self.profile.select_nodes_to_use(self.user, allocated_nodes))
            self.assertTrue(mock_get_synchronised_nodes.called)
            self.assertTrue(mock_select_nodes_from_pool_that_contain_rfport_mo.called)
            self.assertTrue(mock_get_rfport_fdn_list_from_profile_alctd_nodes.called)
            self.assertEqual(mock_update_profile_persistence_nodes_list.call_count, 0)
            self.assertEqual(mock_debug_log.call_count, 4)
            self.assertEqual(mock_get_req_nodes.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "get_required_nodes_from_profile_selected_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "get_rfport_fdn_list_from_profile_allocated_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "select_nodes_from_pool_that_contain_rfport_mo")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.get_synchronised_nodes")
    def test_select_nodes_to_use__when_one_radio_node_existed(self, mock_get_synchronised_nodes,
                                                              mock_select_nodes_from_pool_that_contain_rfport_mo,
                                                              mock_get_rfport_fdn_list_from_profile_alctd_nodes,
                                                              mock_update_profile_persistence_nodes_list,
                                                              mock_debug_log, mock_get_req_nodes):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile."
                   "group_nodes_per_ne_type") as mock_group_nodes_per_ne_type:
            erbs_nodes = self.get_nodes("ERBS", 2)
            radionode_nodes = self.get_nodes("RadioNode", 1)
            allocated_nodes = erbs_nodes + radionode_nodes
            erbs_nodes[0].node_id = "LTE98dg2ERBS00001"
            erbs_nodes[0].node_id = "LTE98dg2ERBS00002"
            radionode_nodes[0].node_id = "LTE03DG200003"
            mock_group_nodes_per_ne_type.return_value = {"ERBS": erbs_nodes, "RadioNode": radionode_nodes}
            mock_get_synchronised_nodes.return_value = [erbs_nodes[0], erbs_nodes[1], radionode_nodes[0]]
            rfort_fdn_list = [u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE98ERBS00001,'
                              u'Equipment=1,FieldReplaceableUnit=1,RfPort=1',
                              u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE98ERBS00002,'
                              u'Equipment=1,FieldReplaceableUnit=1,RfPort=1',
                              u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE03DG200003,'
                              u'Equipment=1,FieldReplaceableUnit=1,RfPort=1']
            mock_get_rfport_fdn_list_from_profile_alctd_nodes.return_value = rfort_fdn_list

            erbs_nodes_that_contain_rfport_mos = {erbs_nodes[0].node_id: {"node": erbs_nodes[0],
                                                                          "rfport": rfort_fdn_list[0]},
                                                  erbs_nodes[1].node_id: {"node": erbs_nodes[1],
                                                                          "rfport": rfort_fdn_list[1]}}
            radionode_nodes_that_contain_rfport_mos = {radionode_nodes[0].node_id: {"node": radionode_nodes[0],
                                                                                    "rfport": rfort_fdn_list[1]}}
            mock_select_nodes_from_pool_that_contain_rfport_mo.side_effect = [radionode_nodes_that_contain_rfport_mos,
                                                                              erbs_nodes_that_contain_rfport_mos]
            nodes_with_ulsa_mos = {"ERBS": erbs_nodes_that_contain_rfport_mos,
                                   "RadioNode": radionode_nodes_that_contain_rfport_mos}
            mock_get_req_nodes.return_value = nodes_with_ulsa_mos, ['LTE03DG200003', 'LTE98dg2ERBS00002', 'id1']

            self.assertEqual(nodes_with_ulsa_mos, self.profile.select_nodes_to_use(self.user, allocated_nodes))
            self.assertTrue(mock_get_synchronised_nodes.called)
            self.assertTrue(mock_select_nodes_from_pool_that_contain_rfport_mo.called)
            self.assertTrue(mock_get_rfport_fdn_list_from_profile_alctd_nodes.called)
            self.assertEqual(mock_update_profile_persistence_nodes_list.call_count, 1)
            self.assertEqual(mock_debug_log.call_count, 5)
            self.assertEqual(mock_get_req_nodes.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "get_required_nodes_from_profile_selected_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "get_rfport_fdn_list_from_profile_allocated_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "select_nodes_from_pool_that_contain_rfport_mo")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.get_synchronised_nodes")
    def test_select_nodes_to_use__if_selected_nodes_not_found(self, mock_get_synchronised_nodes,
                                                              mock_select_nodes_from_pool_that_contain_rfport_mo,
                                                              mock_get_rfport_fdn_list_from_profile_alctd_nodes,
                                                              mock_update_profile_persistence_nodes_list,
                                                              mock_debug_log, mock_get_req_nodes):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile."
                   "group_nodes_per_ne_type") as mock_group_nodes_per_ne_type:
            erbs_nodes = self.get_nodes("ERBS", 2)
            radionode_nodes = self.get_nodes("RadioNode", 1)
            allocated_nodes = erbs_nodes + radionode_nodes
            erbs_nodes[0].node_id = "LTE98dg2ERBS00001"
            erbs_nodes[0].node_id = "LTE98dg2ERBS00002"
            radionode_nodes[0].node_id = "LTE03DG200003"
            mock_group_nodes_per_ne_type.return_value = {"ERBS": erbs_nodes, "RadioNode": radionode_nodes}
            mock_get_synchronised_nodes.return_value = [erbs_nodes[0], erbs_nodes[1], radionode_nodes[0]]
            rfort_fdn_list = [u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE98ERBS00001,'
                              u'Equipment=1,FieldReplaceableUnit=1,RfPort=1',
                              u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE98ERBS00002,'
                              u'Equipment=1,FieldReplaceableUnit=1,RfPort=1',
                              u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE03DG200003,'
                              u'Equipment=1,FieldReplaceableUnit=1,RfPort=1']
            mock_get_rfport_fdn_list_from_profile_alctd_nodes.return_value = rfort_fdn_list

            mock_select_nodes_from_pool_that_contain_rfport_mo.return_value = []
            mock_get_req_nodes.return_value = {}, []
            self.assertEqual({}, self.profile.select_nodes_to_use(self.user, allocated_nodes))
            self.assertTrue(mock_get_synchronised_nodes.called)
            self.assertTrue(mock_select_nodes_from_pool_that_contain_rfport_mo.called)
            self.assertTrue(mock_get_rfport_fdn_list_from_profile_alctd_nodes.called)
            self.assertEqual(mock_update_profile_persistence_nodes_list.call_count, 1)
            self.assertEqual(mock_debug_log.call_count, 7)
            self.assertEqual(mock_get_req_nodes.call_count, 1)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "get_required_nodes_from_profile_selected_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "update_profile_persistence_nodes_list")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "get_rfport_fdn_list_from_profile_allocated_nodes")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile."
           "select_nodes_from_pool_that_contain_rfport_mo")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.get_synchronised_nodes")
    def test_select_nodes_to_use__when_only_radio_nodes_existed(self, mock_get_synchronised_nodes,
                                                                mock_select_nodes_from_pool_that_contain_rfport_mo,
                                                                mock_get_rfport_fdn_list_from_profile_alctd_nodes,
                                                                mock_update_profile_persistence_nodes_list,
                                                                mock_debug_log, mock_get_req_nodes):
        with patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile."
                   "group_nodes_per_ne_type") as mock_group_nodes_per_ne_type:
            radionode_nodes = self.get_nodes("RadioNode", 1)
            radionode_nodes[0].node_id = "LTE03DG200003"
            mock_group_nodes_per_ne_type.return_value = {"RadioNode": radionode_nodes}
            mock_get_synchronised_nodes.return_value = [radionode_nodes[0]]
            rfort_fdn_list = [u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE03DG200003,'
                              u'Equipment=1,FieldReplaceableUnit=1,RfPort=1']
            mock_get_rfport_fdn_list_from_profile_alctd_nodes.return_value = rfort_fdn_list

            radionode_nodes_that_contain_rfport_mos = {radionode_nodes[0].node_id: {"node": radionode_nodes[0],
                                                                                    "rfport": rfort_fdn_list[0]}}
            mock_select_nodes_from_pool_that_contain_rfport_mo.side_effect = [radionode_nodes_that_contain_rfport_mos, []]
            nodes_with_ulsa_mos = {"RadioNode": radionode_nodes_that_contain_rfport_mos}
            mock_get_req_nodes.return_value = nodes_with_ulsa_mos, ['LTE03DG200003']
            self.assertEqual(nodes_with_ulsa_mos, self.profile.select_nodes_to_use(self.user, radionode_nodes))
            self.assertTrue(mock_get_synchronised_nodes.called)
            self.assertTrue(mock_select_nodes_from_pool_that_contain_rfport_mo.called)
            self.assertTrue(mock_get_rfport_fdn_list_from_profile_alctd_nodes.called)
            self.assertEqual(mock_update_profile_persistence_nodes_list.call_count, 0)
            self.assertEqual(mock_debug_log.call_count, 4)
            self.assertEqual(mock_get_req_nodes.call_count, 1)

    # select_nodes_from_pool_that_contain_rfport_mo test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.add_error_as_exception")
    def test_select_nodes_from_pool_that_contain_rfport_mo__returns_nodes_if_rfport_list_no_empty(
            self, mock_add_error_as_exception, mock_debug_log):
        nodes_with_rfport_mos = {}
        erbs_node_name1 = "ERBS_1"
        radionode_node_name = "RadioNode_1"

        erbs_node1 = Mock(node_id=erbs_node_name1, primary_type="ERBS")
        radionode_node = Mock(node_id=radionode_node_name, primary_type="RadioNode")

        nodes = [erbs_node1, radionode_node]

        erbs1_rfport1 = ("SubNetwork=1,MeContext={0},ManagedElement=1,Equipment=1,AuxPlugInUnit=1,DeviceGroup=1,"
                         "RfPort=1".format(erbs_node_name1))
        erbs1_rfport2 = ("SubNetwork=1,MeContext={0},ManagedElement=1,Equipment=1,AuxPlugInUnit=1,DeviceGroup=1,"
                         "RfPort=2".format(erbs_node_name1))
        radionode1_rfport1 = ("ManagedElement={0},Equipment=1,FieldReplaceableUnit=1,RfPort=A"
                              .format(radionode_node_name))
        radionode1_rfport2 = ("ManagedElement={0},Equipment=1,FieldReplaceableUnit=1,RfPort=B"
                              .format(radionode_node_name))

        rfport_fdn_list = [erbs1_rfport1, erbs1_rfport2,
                           radionode1_rfport1, radionode1_rfport2]
        actual_output = self.profile.select_nodes_from_pool_that_contain_rfport_mo("ERBS", nodes, rfport_fdn_list)
        nodes_with_rfport_mos[erbs_node_name1] = {'node': erbs_node1,
                                                  'node_rfport_fdn_list': [erbs1_rfport1, erbs1_rfport2]}
        self.assertEqual(actual_output, nodes_with_rfport_mos)
        self.assertEqual(mock_add_error_as_exception.call_count, 0)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.add_error_as_exception")
    def test_select_nodes_from_pool_that_contain_rfport_mo__on_only_few_nodes(
            self, mock_add_error_as_exception, mock_debug_log):
        nodes_with_rfport_mos = {}
        erbs_node_name1 = "ERBS_1"
        erbs_node_name2 = "ERBS_2"
        erbs_node_name3 = "ERBS_3"
        radionode_node_name = "RadioNode_1"

        erbs_node1 = Mock(node_id=erbs_node_name1, primary_type="ERBS")
        erbs_node2 = Mock(node_id=erbs_node_name2, primary_type="ERBS")
        erbs_node3 = Mock(node_id=erbs_node_name3, primary_type="ERBS")
        radionode_node = Mock(node_id=radionode_node_name, primary_type="RadioNode")

        nodes = [erbs_node1, erbs_node3, erbs_node2, radionode_node]

        erbs1_rfport1 = ("SubNetwork=1,MeContext={0},ManagedElement=1,Equipment=1,AuxPlugInUnit=1,DeviceGroup=1,"
                         "RfPort=1".format(erbs_node_name1))
        erbs1_rfport2 = ("SubNetwork=1,MeContext={0},ManagedElement=1,Equipment=1,AuxPlugInUnit=1,DeviceGroup=1,"
                         "RfPort=2".format(erbs_node_name1))
        erbs1_rfport3 = ("SubNetwork=1,MeContext={0},ManagedElement=1,Equipment=1,AuxPlugInUnit=1,DeviceGroup=1,"
                         "RfPort=2".format(erbs_node_name2))
        erbs1_rfport4 = ("SubNetwork=1,MeContext={0},ManagedElement=1,Equipment=1,AuxPlugInUnit=1,DeviceGroup=1,"
                         "RfPort=2".format(erbs_node_name2))
        radionode_rfport1a = ("ManagedElement={0},Equipment=1,FieldReplaceableUnit=1,RfPort=A"
                              .format(radionode_node_name))
        radionode_rfport1b = ("ManagedElement={0},Equipment=1,FieldReplaceableUnit=1,RfPort=B"
                              .format(radionode_node_name))

        rfport_fdn_list = [erbs1_rfport1, erbs1_rfport2, erbs1_rfport3, erbs1_rfport4,
                           radionode_rfport1a, radionode_rfport1b]
        actual_output = self.profile.select_nodes_from_pool_that_contain_rfport_mo("ERBS", nodes, rfport_fdn_list)
        nodes_with_rfport_mos[erbs_node_name1] = {'node': erbs_node1,
                                                  'node_rfport_fdn_list': [erbs1_rfport1, erbs1_rfport2]}
        nodes_with_rfport_mos[erbs_node_name2] = {'node': erbs_node2,
                                                  'node_rfport_fdn_list': [erbs1_rfport3, erbs1_rfport4]}
        self.assertEqual(actual_output, nodes_with_rfport_mos)
        self.assertEqual(mock_add_error_as_exception.call_count, 0)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.add_error_as_exception")
    def test_select_nodes_from_pool_that_contain_rfport_mo__adds_error_if_rfport_list_empty(
            self, mock_add_error_as_exception, mock_debug_log):
        erbs_node_name = "ERBS_1"
        rbs_node_name = "RBS_1"
        radionode_node_name = "RadioNode_1"

        erbs_node = Mock(node_id=erbs_node_name, primary_type="ERBS")
        rbs_node = Mock(node_id=rbs_node_name, primary_type="RBS")
        radionode_node = Mock(node_id=radionode_node_name, primary_type="RadioNode")

        nodes = [erbs_node, radionode_node, rbs_node]

        self.assertEqual({}, self.profile.select_nodes_from_pool_that_contain_rfport_mo("ERBS", nodes, []))
        self.assertTrue(call(EnvironError("Unable to select ERBS nodes containing RfPort MO") in
                             mock_add_error_as_exception.mock_calls))
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm79profile.Pm79Profile.execute_flow')
    def test_run__in_pm_79_is_successful(self, mock_flow):
        self.pm_79.run()
        self.assertTrue(mock_flow.called)

    # get_rfport_fdn_list_from_profile_allocated_nodes test cases
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.get_rfport_fdn_list_from_enm")
    def test_get_rfport_fdn_list_from_profile_allocated_nodes__is_succesful(self, mock_get_rfport_fdn_list_from_enm,
                                                                            mock_debug_log):
        nodes = [Mock(node_id="LTE02ERBS008", primary_type="ERBS"),
                 Mock(node_id="LTE06DG2003", primary_type="RadioNode")]
        rfort_fdn_list = [u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE02ERBS008,'
                          u'Equipment=1,FieldReplaceableUnit=1,RfPort=1',
                          u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE02ERBS009,'
                          u'Equipment=1,FieldReplaceableUnit=1,RfPort=1',
                          u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE06DG2003,'
                          u'Equipment=1,FieldReplaceableUnit=1,RfPort=1',
                          u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE06DG2005,'
                          u'Equipment=1,FieldReplaceableUnit=1,RfPort=1']
        mock_get_rfport_fdn_list_from_enm.return_value = rfort_fdn_list
        expected_output = [u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE02ERBS008,'
                           u'Equipment=1,FieldReplaceableUnit=1,RfPort=1',
                           u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE06DG2003,'
                           u'Equipment=1,FieldReplaceableUnit=1,RfPort=1']
        self.assertEqual(expected_output, self.profile.get_rfport_fdn_list_from_profile_allocated_nodes(nodes))
        self.assertEqual(mock_get_rfport_fdn_list_from_enm.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 2)

    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.log.logger.debug")
    @patch("enmutils_int.lib.profile_flows.pm_flows.pm79profile.get_rfport_fdn_list_from_enm")
    def test_get_rfport_fdn_list_from_profile_allocated_nodes__if_rfport_fdns_not_found_for_profile_allocated_nodes(
            self, mock_get_rfport_fdn_list_from_enm, mock_debug_log):
        nodes = [Mock(node_id="LTE02ERBS008", primary_type="ERBS"),
                 Mock(node_id="LTE06DG2003", primary_type="RadioNode")]
        rfort_fdn_list = [u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE02ERBS009,'
                          u'Equipment=1,FieldReplaceableUnit=1,RfPort=1',
                          u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE06DG2005,'
                          u'Equipment=1,FieldReplaceableUnit=1,RfPort=1']
        mock_get_rfport_fdn_list_from_enm.return_value = rfort_fdn_list
        self.assertEqual([], self.profile.get_rfport_fdn_list_from_profile_allocated_nodes(nodes))
        self.assertEqual(mock_get_rfport_fdn_list_from_enm.call_count, 1)
        self.assertEqual(mock_debug_log.call_count, 2)

    # get_required_nodes_from_profile_selected_nodes test cases
    @patch('enmutils_int.lib.profile_flows.pm_flows.pm79profile.shuffle')
    def test_get_required_nodes_from_profile_selected_nodes__if_total_selected_nodes_and_selected_nodes_empty(
            self, mock_shuffle):
        self.assertEqual(({}, []), self.profile.get_required_nodes_from_profile_selected_nodes([], {}))
        self.assertFalse(mock_shuffle.called)

    @patch('enmutils_int.lib.profile_flows.pm_flows.pm79profile.shuffle')
    def test_get_required_nodes_from_profile_selected_nodes__is_successful(self, mock_shuffle):
        erbs_nodes = self.get_nodes("ERBS", 2)
        radionode_nodes = self.get_nodes("RadioNode", 2)
        allocated_nodes = radionode_nodes + erbs_nodes
        rfort_fdn_list = [u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE98ERBS00001,'
                          u'Equipment=1,FieldReplaceableUnit=1,RfPort=1',
                          u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE98ERBS00002,'
                          u'Equipment=1,FieldReplaceableUnit=1,RfPort=1',
                          u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE03DG200003,'
                          u'Equipment=1,FieldReplaceableUnit=1,RfPort=1',
                          u'SubNetwork=Europe,SubNetwork=Ireland,SubNetwork=NETSimW,ManagedElement=LTE03DG200004,'
                          u'Equipment=1,FieldReplaceableUnit=1,RfPort=1']
        erbs_nodes_that_contain_rfport_mos = {erbs_nodes[0].node_id: {"node": erbs_nodes[0],
                                                                      "rfport": rfort_fdn_list[0]},
                                              erbs_nodes[1].node_id: {"node": erbs_nodes[0],
                                                                      "rfport": rfort_fdn_list[1]}}
        radionode_nodes_that_contain_rfport_mos = {radionode_nodes[0].node_id: {"node": radionode_nodes[0],
                                                                                "rfport": rfort_fdn_list[2]},
                                                   radionode_nodes[1].node_id: {"node": radionode_nodes[0],
                                                                                "rfport": rfort_fdn_list[3]}}
        selected_nodes = {'RadioNode': radionode_nodes_that_contain_rfport_mos,
                          'EBRS': erbs_nodes_that_contain_rfport_mos}

        total_selected_nodes = [node.node_id for node in allocated_nodes]
        self.profile.get_required_nodes_from_profile_selected_nodes(total_selected_nodes, selected_nodes)
        self.assertTrue(mock_shuffle.called)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
